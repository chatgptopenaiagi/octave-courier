% Octave Courier fixed-operation finite-double worker.
% Project-owned integration code; GNU Octave is an external runtime dependency.
1;

function matrix = decode_matrix (item)
  if (! isscalar (item.rows) || ! isscalar (item.columns) || item.rows < 1 || item.columns < 1 || ...
      item.rows > 256 || item.columns > 256 || item.rows != fix (item.rows) || item.columns != fix (item.columns) || ...
      ! isnumeric (item.values) || ! isreal (item.values) || numel (item.values) != item.rows * item.columns || ...
      any (! isfinite (item.values(:))))
    error ("OctaveCourier:input", "Invalid finite real matrix input");
  endif
  matrix = reshape (item.values, item.columns, item.rows).';
endfunction

args = argv ();
try
  if (numel (args) != 2), error ("OctaveCourier:input", "Expected request and response paths"); endif
  request = jsondecode (fileread (args{1}));
  if (request.schema_version != 1), error ("OctaveCourier:input", "Unsupported request schema"); endif
  response = struct ("schema_version", 1, "operation", request.operation, "octave_version", version ());
  switch (request.operation)
    case {"matrix_product", "solve"}
      a = decode_matrix (request.a); b = decode_matrix (request.b);
      if (strcmp (request.operation, "matrix_product"))
        if (columns (a) != rows (b)), error ("Incompatible product shapes"); endif
        result = a * b;
      else
        if (rows (a) != columns (a) || rows (a) != rows (b)), error ("Incompatible solve shapes"); endif
        if (rcond (a) <= eps * rows (a)), error ("Matrix is singular or numerically ill-conditioned"); endif
        result = a \ b;
        response.residual_inf = norm (a * result - b, Inf);
      endif
      if (! isreal (result) || any (! isfinite (result(:)))), error ("Operation produced nonfinite/complex output"); endif
      response.shape = [rows(result), columns(result)];
      response.values = reshape (result.', 1, []);
    case "packages"
      installed = pkg ("list"); entries = cell (1, numel (installed));
      for k = 1:numel (installed)
        item = installed{k};
        entries{k} = struct ("name", item.name, "version", item.version, "directory", item.dir, "loaded", logical(item.loaded));
      endfor
      response.packages = entries; response.count = numel (entries);
      response.scope = "Installed package registrations only; optional functions are not certified";
    case "numerical"
      integral = quadgk (@sin, 0, pi);
      square_integral = quadgk (@(x) x.^2, 0, 1);
      [root, residual, status] = fzero (@(x) x.^2 - 2, [1, 2]);
      options = odeset ("RelTol", 1e-9, "AbsTol", 1e-11);
      [t, y] = ode45 (@(t,y) -y, [0,1], 1, options);
      assert (abs (integral - 2) < 1e-10 && abs(square_integral - 1/3) < 1e-12 && abs (root - sqrt(2)) < 1e-10 && status > 0 && abs(y(end) - exp(-1)) < 2e-8);
      response.result = struct ("integral_sin_0_pi", integral, "integral_x2_0_1", square_integral, "sqrt2_root", root, "root_residual", residual, "decay_at_one", y(end));
      response.verified = true;
    case "statistics"
      data = decode_matrix (request.data); values = data(:);
      if (numel(values) < 2), error ("Sample statistics needs at least two values"); endif
      if (any(!isfinite([mean(values), median(values), var(values,0), std(values,0)])))
        error ("Statistics produced a nonfinite result");
      endif
      response.result = struct ("count", numel(values), "mean", mean(values), "median", median(values), "sample_variance", var(values,0), "sample_std", std(values,0));
      response.scope = "Descriptive sample statistics; variance/std normalize by N-1";
    case "signal"
      transform = fft ([1,0,0,0]); filtered = filter ([0.5,0.5], 1, ones(1,4)); convolution = conv ([1,2], [1,1]);
      assert (norm (transform - ones(1,4), Inf) < 1e-12 && norm(filtered - [0.5,1,1,1], Inf) < 1e-12 && isequal(convolution,[1,3,2]));
      response.result = struct ("fft_real", real(transform), "fft_imag", imag(transform), "fir_filter", filtered, "convolution", convolution);
      response.verified = true;
    case "optimization"
      [location, objective, status] = fminbnd (@(x) (x-3).^2+7, -5, 7, optimset ("TolX", 1e-10));
      assert (abs(location - 3) < 1e-6 && abs(objective - 7) < 1e-10 && status > 0);
      response.result = struct ("location", location, "objective", objective, "status", status);
      response.verified = true;
    case "plot"
      toolkits = available_graphics_toolkits ();
      if (! any(strcmp(toolkits,"gnuplot"))), error ("Headless PNG export requires the gnuplot Octave graphics toolkit"); endif
      graphics_toolkit ("gnuplot"); set (0, "defaultfigurevisible", "off");
      figure_handle = figure ("visible", "off");
      unwind_protect
        graphics_toolkit (figure_handle, "gnuplot");
        x = linspace (0, 2*pi, 101); plot (x, sin(x), "linewidth", 2);
        xlabel ("x (radians)"); ylabel ("sin(x)"); title ("Octave Courier: sine demonstration"); grid on;
        print (figure_handle, request.output, "-dpng", "-r100");
      unwind_protect_cleanup
        close (figure_handle);
      end_unwind_protect
      response.toolkit = "gnuplot";
      response.scope = "One owned sine PNG; interactive GUI not tested";
    otherwise
      error ("OctaveCourier:operation", "Unsupported fixed operation");
  endswitch
  if (exist (args{2}, "file")), error ("Response path already exists"); endif
  handle = fopen (args{2}, "w");
  if (handle < 0), error ("Could not create response file"); endif
  unwind_protect
    fprintf (handle, "%s\n", jsonencode (response));
  unwind_protect_cleanup
    fclose (handle);
  end_unwind_protect
catch failure
  fprintf (stderr, "OCTAVE_COURIER_ERROR: %s\n", failure.message);
  exit (1);
end_try_catch
