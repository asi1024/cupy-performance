import inspect
import itertools

import cupyx
import gc


class Runner(object):

    def __init__(self, benchmark):
        self.benchmark = benchmark

    def _create_key_from_args(self, case, arg_names):
        benchmark = self.benchmark
        if hasattr(benchmark, 'args_key'):
            case = {arg_names[i]: arg for i, arg in enumerate(case)}
            return getattr(benchmark, 'args_key')(**case)
        if type(case) in (list, tuple) and len(case) == 1:
            return self._create_key_from_args(case[0], arg_names)
        return str(case)

    def run(self, report, xp):
        benchmark = self.benchmark
        object_methods = [method_name
                          for method_name in dir(benchmark)
                          if 'time_' in method_name]
        if hasattr(benchmark, 'setup'):
            arg_names = inspect.getfullargspec(benchmark.setup).args[3:]
        args = [getattr(benchmark, arg) for arg in arg_names]
        for method_name in object_methods:
            method = getattr(benchmark, method_name)
            # ignore self
            bench_times = {}

            # Do combinations of the lists
            cases = itertools.product(*args)
            for case in cases:
                kwargs = {name: arg for name, arg in zip(arg_names, case)}
                if hasattr(benchmark, 'setup'):
                    benchmark.setup(method_name, xp, **kwargs)
                key = self._create_key_from_args(case, arg_names)
                print('{:20} - case {:10}'.format(method_name, key), end='')
                times = cupyx.time.repeat(method, n=5, n_warmup=10, name='')
                bench_times[key] = {'cpu': times.cpu_times,
                                    'gpu': times.gpu_times}
                print(times)
            report(method_name, bench_times)
        if hasattr(benchmark, 'teardown'):
            benchmark.teardown()
        gc.collect()
