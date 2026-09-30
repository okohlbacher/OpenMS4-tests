// Copyright (c) 2002-present, OpenMS Inc. -- EKU Tuebingen, ETH Zurich, and FU Berlin
// SPDX-License-Identifier: BSD-3-Clause
// $Maintainer: OpenMS Team $
#include <OpenMS/APPLICATIONS/ToolHandler.h>
#include <OpenMS/CHEMISTRY/AASequence.h>
#include <OpenMS/CHEMISTRY/EmpiricalFormula.h>
#include <OpenMS/CONCEPT/VersionInfo.h>
#include <OpenMS/FORMAT/MzMLFile.h>
#include <OpenMS/KERNEL/MSExperiment.h>
#include <OpenMS/SYSTEM/File.h>
#include <cmath>
#include <dlfcn.h>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>

int main(int argc, char** argv)
{
  if (argc != 2) { return 1; }
  const auto prefix = std::filesystem::canonical(argv[1]);
  Dl_info location {};
  if (!dladdr(reinterpret_cast<const void*>(&OpenMS::VersionInfo::getBuildInfo), &location)) { return 2; }
  const auto library = std::filesystem::canonical(location.dli_fname);
  const auto relative = library.lexically_relative(prefix);
  if (relative.empty() || *relative.begin() == "..") { return 3; }
  const auto data = std::filesystem::canonical(OpenMS::File::getOpenMSDataPath());
  if (data != prefix / "share/OpenMS/4.0.0") { return 4; }
  std::ifstream metadata(prefix / "share/openms4/OpenMSBuildInfo.json");
  std::string expected(std::istreambuf_iterator<char>{metadata}, {});
  if (!expected.empty() && expected.back() == '\n') { expected.pop_back(); }
  if (OpenMS::VersionInfo::getBuildInfo() != expected || OpenMS::VersionInfo::isSourceDirty()) { return 5; }
  const double glucose = OpenMS::EmpiricalFormula("C6H12O6").getMonoWeight();
  const double oxidation = OpenMS::AASequence::fromString("M(Oxidation)PEPTIDE").getMonoWeight()
                        - OpenMS::AASequence::fromString("MPEPTIDE").getMonoWeight();
  if (std::abs(glucose - 180.063388104) > 1e-5 || std::abs(oxidation - 15.99491462) > 1e-5) { return 6; }
  OpenMS::MSSpectrum spectrum;
  spectrum.setRT(12.5);
  spectrum.setMSLevel(1);
  OpenMS::Peak1D peak;
  peak.setMZ(200.0); peak.setIntensity(42.0); spectrum.push_back(peak);
  peak.setMZ(100.0); peak.setIntensity(21.0); spectrum.push_back(peak);
  spectrum.sortByPosition();
  OpenMS::MSExperiment original, restored;
  original.addSpectrum(spectrum);
  OpenMS::MzMLFile().store("runtime-roundtrip.mzML", original);
  OpenMS::MzMLFile().load("runtime-roundtrip.mzML", restored);
  if (restored.size() != 1 || restored[0].size() != 2 || restored[0].getRT() != 12.5 ||
      restored[0][0].getMZ() != 100.0 || restored[0][1].getIntensity() != 42.0) { return 7; }
  const auto file_info = std::filesystem::canonical(OpenMS::ToolHandler::findExecutable("FileInfo"));
  if (file_info != prefix / "bin/FileInfo") { return 8; }
  std::cout << "RUNTIME_IDENTITY_JSON\n{\"core\":" << OpenMS::VersionInfo::getBuildInfo()
            << ",\"loaded_library\":" << std::quoted(library.string())
            << ",\"data_directory\":" << std::quoted(data.string())
            << ",\"file_info\":" << std::quoted(file_info.string())
            << ",\"registered_tools\":" << OpenMS::ToolHandler::getTOPPToolList().size()
            << ",\"glucose_mono_mass\":" << std::setprecision(15) << glucose
            << ",\"oxidation_delta\":" << oxidation << "}\n";
}
