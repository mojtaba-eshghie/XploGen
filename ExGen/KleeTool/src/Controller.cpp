//
// Created by xxxx on xxxx/xx/xx.
//

#include "Controller.h"

#include "ModifyLLVM.h"

#include <unistd.h>

bool Controller::ParseJson(const string& folderName) {
  string thisPath = path + "/" + folderName;
  vector<string> jsonFiles;
  string jsonPath = path + "/" + folderName + "/" + folderName + ".json";
  // if there is no json files
  if (!GetTargetFiles(thisPath, jsonFiles, ".json")) {
    cout << "No json file\n";
    return false;
  }
  if (jsonFiles.empty()) {
    cout << "No json file\n";
    return false;
  }

  for (int i = 0; i < jsonFiles.size(); i++) {
    if (jsonFiles[i].find("_wasm.json") != string::npos ||
        i == jsonFiles.size() - 1) {
      jsonPath = path + "/" + folderName + "/" + jsonFiles[i];
      break;
    }
  }
  // read from json file
  ifstream inFile(jsonPath, ios::in);

  // read json in binary data
  ostringstream buf;
  char ch;
  while (buf && inFile.get(ch)) buf.put(ch);

  // file stream point refresh
  inFile.clear();
  inFile.seekg(0, ios::beg);

  // parse json
  document.Parse(buf.str().c_str());
  inFile.close();

  return true;
}

bool Controller::GetFiles() {
  DIR* dir;
  struct dirent* ptr;

  if ((dir = opendir(path.c_str())) == nullptr) {
    perror("Open dir error...");
    return false;
  }

  while ((ptr = readdir(dir)) != nullptr) {
    if (strcmp(ptr->d_name, ".") == 0 || strcmp(ptr->d_name, "..") == 0 ||
        ptr->d_type == 10)  /// current dir OR parent dir OR link file
      continue;
    else if (ptr->d_type == 4 || ptr->d_type == 8)  /// dir | file
      folderNames.emplace_back(ptr->d_name);
  }
  closedir(dir);

  return true;
}

bool Controller::GetFiles(const string& _path, vector<string>& _folderNames) {
  DIR* dir;
  struct dirent* ptr;

  if ((dir = opendir(_path.c_str())) == nullptr) {
    perror("Open dir error...");
    return false;
  }

  while ((ptr = readdir(dir)) != nullptr) {
    if (strcmp(ptr->d_name, ".") == 0 || strcmp(ptr->d_name, "..") == 0 ||
        ptr->d_type == 10)  /// current dir OR parent dir OR link file
      continue;
    else if (ptr->d_type == 4 || ptr->d_type == 8)  /// dir | file
      _folderNames.emplace_back(ptr->d_name);
  }
  closedir(dir);

  return true;
}

void Controller::Entry() {
  if (GetFiles()) {
    for (const auto& folderName : folderNames) {
      if (folderName.find(R"(.py)") != string::npos ||
          folderName.find(R"(.sh)") != string::npos)
        continue;

      string thisPath = path + "/" + folderName;
      cout << "This path is " << thisPath << endl;

      // only func not yet run have to go on
      if (access((thisPath + "/time.txt").c_str(), 0) == -1) {
        // start
        start_t = clock();
        // There is a json
        if (ParseJson(folderName)) FunChains(folderName);

        // The end of the timing
        end_t = clock();
        // The output of time
        double endtime = (double)(end_t - start_t) / CLOCKS_PER_SEC;
        ofstream out(path + "/" + folderName + "/time.txt");
        out << "time = " << endtime << " s" << endl;
      } else
        cout << "All Done!" << endl;
    }
  }
}

void Controller::FunChains(const string& folderName) {
  assert(document.IsArray());
  int limitInsts = 0;
  // document.size is the number of call chains
  funcChains->InitChains(document.Size());
  // Added LL file path detection for EOS platform
  vector<string> llFiles;
  string llFileName;
  if (!GetTargetFiles(path + "/" + folderName, llFiles, "ll")) {
    cout << "No llvm file\n";
    return;
  }
  if (llFiles.empty()) {
    cout << "No ll file\n";
    return;
  }

  if (find(llFiles.begin(), llFiles.end(), "tmp.ll") != llFiles.end())
    llFiles.erase(find(llFiles.begin(), llFiles.end(), "tmp.ll"));
  for (int i = 0; i < llFiles.size(); i++) {
    if (llFiles[i].find("_wasm.ll") != string::npos ||
        i == llFiles.size() - 1) {
      llFileName = llFiles[i];
      break;
    }
  }
  // Initialize modify LLVM correlation
  ModifyLLVM modifyLlvm(llFileName, path + "/" + folderName, document.Size());
  LLVMFile* thisLLVMFile = modifyLlvm.GetLLVMFile();
  cout << "file name = " << thisLLVMFile->GetFileName() << endl;

  int chainIndex = 0;
  // Each loop is a call chain
  for (auto& funChain : document.GetArray()) {
    cout << "/////// Function Chain " << to_string(chainIndex) << " ///////"
         << endl;
    assert(funChain.IsArray());
    FuncChain thisChain = funcChains->GetChain(chainIndex);
    thisChain.InitFunc(funChain.Size());

    // cout << "debug: 1" << endl;
    // TODO can locate the call chain in the file here
    // The goal of a location is to reduce IO time but in fact the best way is
    // to get it all in one step LLVMFuncChain thisLLVMChain =
    // thisLLVMFile->GetLLVMChain(chainIndex);
    // thisLLVMChain.Init(funChain.Size());

    // Each of these loops is a function
    int funcIndex = 0;
    for (auto& funPtr : funChain.GetArray()) {
      Function thisFunc = thisChain.GetFunction(funcIndex);
      thisFunc.SetFuncName(funPtr.MemberBegin()->value.GetString());

      assert((funPtr.MemberBegin() + 1)->value.IsArray());

      thisFunc.InitInsts((funPtr.MemberBegin() + 1)->value.Size());
      // cout << "funcName = " << thisFunc.GetFuncName() << endl;

      // Read into the function file
      string funcName = thisFunc.GetFuncName();  // cout << funcName << endl;
      LLVMFunction thisLLVMFunc = thisLLVMFile->InitFuncLines(funcName);
      // thisLLVMFunc.Show();

      int instNum = 0;
      // Each loop is an instruction
      for (auto& inst : (funPtr.MemberBegin() + 1)->value.GetArray()) {
        assert(inst.IsObject());
        Instruction thisInst = thisFunc.GetInst(instNum);
        thisInst.InitInst((inst.MemberBegin() + 1)->value.GetString());
        // output this instruction
        //        cout << thisInst.GetType() << ": " << thisInst.GetString() <<
        //        endl;

        // Klee_assume is used when the instruction is an arithmetic operation
        // global variables need to be symbolic
        if (thisInst.GetType() == 1) {
          auto arithInst = static_cast<ArithOp*>(thisInst.GetInst());
          string instStr = (inst.MemberBegin() + 1)->value.GetString();

          int opType =
              arithInst->GetOp() == "add" || arithInst->GetOp() == "mul" ? 1 :
                                                                           2;

          thisLLVMFunc.AddAssume(3 - opType, instNum * 3 + 0,
                                 arithInst->GetReg(2), arithInst->GetReg(2),
                                 arithInst->GetString(), false);
          thisLLVMFunc.AddAssume(3 - opType, instNum * 3 + 1,
                                 arithInst->GetReg(3), arithInst->GetReg(2),
                                 arithInst->GetString(), false);
          thisLLVMFunc.AddAssume(opType + 0, instNum * 3 + 2,
                                 arithInst->GetReg(1), arithInst->GetReg(2),
                                 arithInst->GetString(), true);

          thisFunc.SetIsArith(true);
        } else if (thisInst.GetType() == 2) {
          auto callInst = static_cast<FuncCall*>(thisInst.GetInst());

          // TODO we need to make symbolize on call func args (next ver)
          // TODO we need to make symbolize on this func args (next version)

          thisFunc.SetIsCall(true);
        } else if (thisInst.GetType() == 3) {
          auto storeInst = static_cast<StoreInst*>(thisInst.GetInst());

          // thisLLVMFile->AddGlobalSymbols(storeInst->GetDest());
          // symbolic `store global variables`
          thisLLVMFunc.WriteNewLines(
              modifyLlvm.ModifyStoreInst(storeInst, thisLLVMFunc));
          // cout << "debug: " << thisLLVMFile->symCount << endl;
          thisFunc.SetIsInit(true);
        }
        thisFunc.ReturnInst(instNum, thisInst);
        instNum++;
      }
      // cout << "debug: 2" << endl;
      // replace this funclines in llvm ir file
      thisLLVMFile->Replace(thisLLVMFunc.StartLine(), thisLLVMFunc.EndLine(),
                            thisLLVMFunc.GetNewLines());
      thisLLVMFile->ReturnLLFunc(funcName, thisLLVMFunc);

      thisChain.ReturnFunction(funcIndex, thisFunc);
      funcIndex++;
      // limitInsts += (funPtr.MemberBegin() + 1)->value.GetArray().Size();
    }
    // cout << "debug: 3" << endl;
    // find out start func in this call chain
    Function& startFunc = thisChain.ReturnChainStart();
    // add global symbols and local symbols
    LLVMFunction tmpLLFunc =
        thisLLVMFile->InitFuncLines(startFunc.GetFuncName());
    int argCount = thisLLVMFile->AddLocalSymDecl(tmpLLFunc);
    // thisLLVMFile->WriteGlobalSymDecl();

    // find out the end func in this call chain
    cout << "debug: 3.1" << endl;
    string endFuncName = thisChain.GetFunction(0).GetFuncName();
    vector<KleeAssume> assumes =
        thisLLVMFile->GetLLFuncs()[endFuncName].GetAssumes();
    // cout << "debug: 3.2" << endl;
    LLVMFunction thisLLVMFunc = thisLLVMFile->InitFuncLines(endFuncName);
    thisLLVMFile->SetTmpLines();
    // cout << "debug: 3.3" << endl;
    //    vector<string> newStr =
    //        modifyLlvm.AddArithGlobalSyms(thisLLVMFunc,
    //        assumes.front().GetInst());

    // thisLLVMFile->WriteGlobalSymDecl();
    // ! each instruction need to run KLEE once
    cout << "debug: 4" << endl;
    for (int i = 0; i < (assumes.size() + 1) / 3; i++) {
      vector<KleeAssume> tmpAssumes(assumes.begin() + (3 * i),
                                    assumes.begin() + (3 * i + 3));
      vector<string> newStr =
          modifyLlvm.AddArithGlobalSyms(thisLLVMFunc, tmpAssumes[0].GetInst());

      bool isWasnRtStack = false;

      if (!newStr.empty())
        if (newStr.front() == "@wasm_rt_call_stack_depth") {
          isWasnRtStack = true;
          cout << "skip @wasm_rt_call_stack_depth!" << endl;
        }

      if (!isWasnRtStack) {
        thisLLVMFunc.WriteNewLines(
            modifyLlvm.ModifyAssumes(thisLLVMFunc, tmpAssumes, newStr));
        thisLLVMFile->Replace(thisLLVMFunc.StartLine(), thisLLVMFunc.EndLine(),
                              thisLLVMFunc.GetNewLines());
        // cout << "debug: 5" << endl;
        // inert global symbols' symbolic declaration
        thisLLVMFile->WriteGlobalSymDecl();
        // cout << "debug: 6" << endl;
        thisLLVMFile->CreateFile("tmp.ll");
        // call `klee --entry-point=thisFuncName`
        // if (thisLLVMFile->symCount == argCount) {
        RunKlee(startFunc.GetFuncName(), folderName,
                tmpAssumes.front().GetInst(), to_string(i),
                to_string(chainIndex));
        bool hasSolution = ExtractInfo(startFunc.GetFuncName(), folderName,
                                       tmpAssumes.front().GetInst(),
                                       to_string(i), to_string(chainIndex));
        limitInsts++;
        if (hasSolution) {
          cout << "Find Solution!" << endl;
          // return;
        }
        if (limitInsts > 1500) {
          cout << "Limited instructions!" << endl;
          // return;
        }
        cout << "Run klee " << limitInsts << " times" << endl;
        // } else
        // cout << "lack of func args symbol" << endl;
      }
      // TODO need to find out constructions and call KLEE

      thisLLVMFunc.Refresh();
      thisLLVMFile->RefreshLines();
      // cout << "debug: 7" << endl;
      //       exit(0);
    }
    //    exit(0);
    thisLLVMFile->Refresh();
    chainIndex++;
  }
}
