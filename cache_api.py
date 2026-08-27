# Copyright 2025 Mohamed Gaber
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import json
import argparse

from pathlib import Path

from ciel import Family
from ciel.source import GitHubReleasesDataSource
from ciel.common import mkdirp, date_to_iso8601

parser = argparse.ArgumentParser(
    description="A program that takes an output directory and a single input."
)
parser.add_argument("-O", "--output_dir", help="The directory to write output to")
parser.add_argument(
    "target_repo", help="The target input repo (in the format <owner>/<repo>)"
)

args = parser.parse_args()

download_path = Path(args.output_dir)
data_source = GitHubReleasesDataSource(args.target_repo)
for pdk in ["ihp-sg13", "sky130", "gf180mcu"]:
    family = Family.by_name[pdk]

    versions = data_source.get_available_versions(pdk)
    base = download_path / pdk
    mkdirp(base)
    manifest_versions = []
    for version in versions:
        entry = {
            "version": version.name,
            "date": date_to_iso8601(version.commit_date),
        }
        if version.prerelease:
            entry["prerelease"] = True
        manifest_versions.append(entry)
    manifest = {"version": 1, "pdk": pdk, "versions": manifest_versions}
    with open(base / "manifest.json", "w") as f:
        json.dump(manifest, f)
    for version in versions:
        version_manifest = {"version": 1, "assets": []}
        version_base = base / version.name
        mkdirp(version_base)
        _, assets = data_source.get_downloads_for_version(version)
        for asset in assets:
            version_manifest["assets"].append(asset.__dict__)
        with open(version_base / "manifest.json", "w") as f:
            json.dump(version_manifest, f)

    for variant in family.variants:
        target = download_path / variant

        # Need this check because theoretically PDK and family names could be
        # the same
        if not target.exists():
            os.symlink(family.name, target)
