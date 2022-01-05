/*
 * The MIT License (MIT)
 * 
 * Copyright (c) 2018-2022 Yury Gribov
 * 
 * Use of this source code is governed by The MIT License (MIT)
 * that can be found in the LICENSE.txt file.
 */

#include <clang-c/Index.h>

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include <libgen.h>
#include <getopt.h>
#include <unistd.h>

#include <string>
#include <vector>
#include <set>

struct Symbol {
  std::string Name, MangledName;
};

struct InterfaceInfo {
  int Verbose;
  const std::string &Root;
  const std::set<std::string> OnlyHdrs;
  std::vector<Symbol> Syms;
  bool HasClasses;
  InterfaceInfo(int Verbose, const std::string &Root, const std::set<std::string> &OnlyHdrs)
    : Verbose(Verbose), Root(Root), OnlyHdrs(OnlyHdrs), HasClasses(false) {}
};

static std::string ToStr(CXString CXS) {
  const char *CStr = clang_getCString(CXS);
  std::string Str(CStr);
  clang_disposeString(CXS);
  return Str;
}

static std::string RealPath(const char *p) {
  char *tmp = realpath(p, 0);
  if (!tmp) {
    fprintf(stderr, "File %s not found\n", p);
    exit(1);
  }
  std::string Res(tmp);
  free(tmp);
  return Res;
}

static std::string ParseLoc(CXSourceLocation Loc, unsigned *Line, bool Expansion) {
  CXFile F;
  (Expansion ? clang_getExpansionLocation : clang_getSpellingLocation)(Loc, &F, Line, 0, 0);
  return RealPath(ToStr(clang_getFileName(F)).c_str());
}

static bool IsUnderRoot(const std::string &Filename, const std::string &Root) {
  return 0 == Filename.compare(0, Root.size(), Root);
}

static enum CXChildVisitResult collectDecls(CXCursor C, CXCursor Parent, CXClientData Data) {
  (void)Parent;
  InterfaceInfo *Info = (InterfaceInfo *)Data;

#if 0
  {
    std::string KindStr = ToStr(clang_getCursorKindSpelling(clang_getCursorKind(C)));
    fprintf(stderr, "Got %s\n", KindStr.c_str());
  }
#endif

  // Skip host includes
  CXSourceLocation Loc = clang_getCursorLocation(C);
  unsigned Line;
  std::string ExpFilename = ParseLoc(Loc, &Line, true);
  std::string SpellFilename = ParseLoc(Loc, &Line, false);
  if (!IsUnderRoot(SpellFilename, Info->Root)) {
    if (Info->Verbose)
      fprintf(stderr, "note: skipping declaration at %s:%u (not under %s)\n",
              SpellFilename.c_str(), Line, Info->Root.c_str());
    return CXChildVisit_Continue;
  } else if (!Info->OnlyHdrs.empty() && !Info->OnlyHdrs.count(SpellFilename)) {
    if (Info->Verbose)
      fprintf(stderr, "note: skipping declaration at %s:%u (not in list of headers)\n",
              SpellFilename.c_str(), Line);
    return CXChildVisit_Continue;
  }

#if 0
  fprintf(stderr, "In file %s:%u\n", ExpFilename.c_str(), Line);
#endif

  switch (C.kind) {
  // TODO: handle C++ methods
  // TODO: ignore static functions/vars
  case CXCursor_FunctionDecl:
  case CXCursor_CXXMethod:
  case CXCursor_Constructor:
  case CXCursor_Destructor:
  case CXCursor_VarDecl: {
      std::string Name = ToStr(clang_getCursorSpelling(C)),
        MangledName = ToStr(clang_Cursor_getMangling(C));
      if (Info->Verbose)
        fprintf(stderr, "note: found symbol %s (expanded in %s, spelled in %s)\n",
                Name.c_str(), ExpFilename.c_str(), SpellFilename.c_str());
      Info->Syms.push_back({Name, MangledName});
      break;
    }
  case CXCursor_ClassDecl:
    Info->HasClasses = true;
    return CXChildVisit_Recurse;
  case CXCursor_Namespace:
    return CXChildVisit_Recurse;
  default:
    break;
  }

  return CXChildVisit_Continue;
}

static void usage(const char *prog) {
  printf("\
Usage: %s [OPT]... HDR...\n\
Print APIs provided by header(s).\n\
\n\
Options:\n\
  -h, --help                 Print this help and exit.\n\
  -v, --verbose              Enable debug prints.\n\
  -c FLAGS, --cflags FLAGS   Specify CFLAGS to use.\n\
  -r ROOT, --root ROOT       Only consider symbols which are defined\n\
                             in files under ROOT.\n\
  --only A.H,B.H,...         Report only functions in these headers.\n\
  --only-args                Report only functions in HDRs\n\
", prog);
  exit(0);
}

int main(int argc, char *argv[]) {
  const char *me = basename((char *)argv[0]);

  std::string Flags, Root;
  std::set<std::string> OnlyHdrs;
  int Verbose = 0;
  bool OnlyArgs = false;
  while (1) {
    static struct option long_opts[] = {
      {"verbose", no_argument, 0, 'v'},
      {"cflags", required_argument, 0, 'c'},
      {"root", required_argument, 0, 'r'},
      {"help", required_argument, 0, 'h'},
#     define OPT_ONLY 1
      {"only", required_argument, 0, OPT_ONLY},
#     define OPT_ONLY_ARGS 2
      {"only-args", no_argument, 0, OPT_ONLY_ARGS},
    };

    int opt_index = 0;
    int c = getopt_long(argc, argv, "vc:r:h", long_opts, &opt_index);

    if (c == -1)
      break;

    switch (c) {
    case 'v':
      ++Verbose;
      break;
    case 'c':
      Flags = optarg;
      break;
    case 'r':
      if (access (optarg, F_OK) == -1) {
        fprintf(stderr, "Directory %s does not exist\n", optarg);
        exit(1);
      }
      Root = RealPath(optarg);
      break;
    case 'h':
      usage(me);
      break;
    case OPT_ONLY: {
        char *hdrs = optarg;
        char *rest = NULL;
        while (char *hdr = strtok_r(hdrs, " \t,", &rest)) {
          hdrs = NULL;
          OnlyHdrs.insert(RealPath(hdr));
        }
        break;
      }
    case OPT_ONLY_ARGS:
      OnlyArgs = true;
      OnlyHdrs.clear();
      break;
    default:
      abort();
    }
  }

  std::vector<const char *> FlagsArray;
  for (size_t End = 0; End < std::string::npos; ) {
    size_t Begin = Flags.find_first_not_of(" \t", End);
    if (Begin == std::string::npos)
      break;
    End = Flags.find_first_of(" \t", Begin + 1);
    if (End != std::string::npos)
      Flags[End++] = 0;
    FlagsArray.push_back(&Flags[Begin]);
  }

  if (optind >= argc) {
    fprintf(stderr, "error: no headers specified in command line...");
    return 0;
  }

  if (OnlyArgs) {
    for (int I = optind; I < argc; ++I)
      OnlyHdrs.insert(RealPath(argv[I]));
  }

  std::set<std::string> Names;
  for (int I = optind; I < argc; ++I) {
    std::string Hdr = argv[I];

    CXIndex Idx = clang_createIndex(0, 0);
    CXTranslationUnit Unit = clang_parseTranslationUnit(
      Idx, Hdr.c_str(), FlagsArray.empty() ? 0 : &FlagsArray[0],
      FlagsArray.size(), 0, 0, CXTranslationUnit_None);
    if (!Unit) {
      fprintf(stderr, "error: failed to read file %s\n", Hdr.c_str());
      exit(1);
    }

    bool AnyError = false;
    for (unsigned J = 0, N = clang_getNumDiagnostics(Unit); J != N; ++J) {
      CXDiagnostic D = clang_getDiagnostic(Unit, J);
      clang_disposeDiagnostic(D);
      CXDiagnosticSeverity S = clang_getDiagnosticSeverity(D);
      if (S >= CXDiagnostic_Error || (S >= CXDiagnostic_Warning && Verbose)) {
        std::string Msg = ToStr(clang_formatDiagnostic(D, clang_defaultDiagnosticDisplayOptions()));
        fprintf(stderr, "%s\n", Msg.c_str());
      }
      AnyError |= S >= CXDiagnostic_Error;
    }

    if (AnyError)
      return 1;

    std::string HdrRoot = Root;
    if (HdrRoot.empty()) {
      size_t J = Hdr.find("/include/");
      if (J == std::string::npos)
        fprintf(stderr, "Failed to determine include root for %s\n", Hdr.c_str());
      else
        HdrRoot = Hdr.substr(0, J) + "/include";
    }

    InterfaceInfo Info(Verbose, HdrRoot, OnlyHdrs);
    clang_visitChildren(clang_getTranslationUnitCursor(Unit), collectDecls, (CXClientData)&Info);

    if (Info.HasClasses)
      fprintf(stderr, "warning: C++ is not fully supported, interface info may be incomplete\n");

    if (Verbose) {
      fprintf(stderr, "APIs exported from %s:\n", Hdr.c_str());
      for (auto &Sym : Info.Syms) {
        fprintf(stderr, "  %s (%s)\n", Sym.MangledName.c_str(), Sym.Name.c_str());
      }
    }

    for (auto &Sym : Info.Syms)
      Names.insert(Sym.MangledName);

    clang_disposeTranslationUnit(Unit);
    clang_disposeIndex(Idx);
  }

  for (auto &Name : Names)
    printf("%s\n", Name.c_str());

  return 0;
}
