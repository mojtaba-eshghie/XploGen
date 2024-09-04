//
// Created by xxxx on xxxx/xx/xx.
//
#include "Controller.h"
//#include "ModifyLLVM.h"

int main(int argc, char** argv) {
  if (argc == 1) {
    cout << "Need folder!" << endl;
    return 1;
  }

  string path = argv[1];

  Controller controller(path);
  controller.Entry();

  return 0;
}
