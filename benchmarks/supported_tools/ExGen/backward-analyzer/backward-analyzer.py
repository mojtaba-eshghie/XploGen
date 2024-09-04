import os, sys, datetime
from pts import PartiallyTxnSet

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 backward-analyzer.py <dataset path> <log file path> <vulnerability type>")
        sys.exit()
    
    dataset_path = sys.argv[1]
    logfile_path = sys.argv[2]
    vul_type = sys.argv[3] # 1. intflow 2. reentrancy 3. teether

    execute_time = {}

    for parent, dirnames, filenames in os.walk(dataset_path):
        for filename in filenames:
            prefix = os.path.splitext(filename)[0]
            suffix = os.path.splitext(filename)[-1]
            if suffix == ".ll":
                start = datetime.datetime.now()
                llvm_filepath = "%s.ll" % os.path.join(parent, prefix)
                json_filepath = "%s.json" % os.path.join(parent, prefix)
                pts = PartiallyTxnSet(llvm_filepath, vul_type)
                res_json = pts.pts_constructor()
                with open(json_filepath, "w") as wf:
                    wf.write(res_json)
                end = datetime.datetime.now()
                duration = end - start
                execute_time[llvm_filepath] = duration.total_seconds() * 1000

    with open(logfile_path, "w") as f:
        for key in execute_time:
            f.write("%s analyzed in %d milliseconds\n" % (key, execute_time[key]))
