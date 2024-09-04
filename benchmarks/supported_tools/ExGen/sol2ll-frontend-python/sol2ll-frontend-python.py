import os, sys, datetime
from codegen.codegen import LLVMCodeGenerator

if __name__ == "__main__":
    '''
    cg = LLVMCodeGenerator("simple.sol")
    cg.generate_code()
    cg.print_ir()
    '''
    
    if len(sys.argv) != 3:
        print("Usage: python3 sol2ll-frontend-python.py <dataset path> <log file path>")
        sys.exit()

    dataset_path = sys.argv[1]
    logfile_path = sys.argv[2]

    count = 0
    execute_time = {}

    for parent, dirnames, filenames in os.walk(dataset_path):
        for filename in filenames:
            filepath = os.path.join(parent, filename)
            if filepath.endswith(".sol"):
                start = datetime.datetime.now()
                try:
                    cg = LLVMCodeGenerator(filepath)
                    cg.generate_code()
                    ll_filepath = filepath.replace(".sol", ".ll")
                    with open(ll_filepath, "w") as f:
                        for key in cg.modules:
                            f.write(cg.modules[key].__repr__())
                    count = count + 1
                except:
                    pass
                end = datetime.datetime.now()
                duration = end - start
                execute_time[filepath] = duration.total_seconds() * 1000
    with open(logfile_path, "w") as f:
        f.write("SUCCESSFULLY COMPILED: %d\n\n" % count)
        for key in execute_time:
            f.write("%s compiled in %d milliseconds\n" % (key, execute_time[key]))
