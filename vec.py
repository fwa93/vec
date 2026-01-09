#!/usr/bin/env python3

import argparse
import os
import csv
from collections import defaultdict


TAXONOMY_COLUMNS = [
    "species",
    "genus",
    "family",
    "order",
    "class",
    "phylum",
    "superkingdom",
]


def read_report(path):
    """
    Read a report file and return:
    - sample_names: list of sample columns
    - data: dict {species -> {sample -> abundance}}
    """
    data = defaultdict(dict)

    with open(path, newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)

        try:
            sample_start = header.index("superkingdom") + 1
        except ValueError:
            raise ValueError("Column 'superkingdom' not found in header")

        sample_names = header[sample_start:]
        rows = list(reader)

        for idx, row in enumerate(rows):
            if not row:
                continue

            # Force last line to be Unassigned
            if idx == len(rows) - 1:
                species = "Unassigned"
            else:
                species = row[0].strip()

            for i, sample in enumerate(sample_names):
                value = row[sample_start + i].strip()
                abundance = float(value) if value else 0.0
                data[species][sample] = abundance

    return sample_names, data


def compare_reports(reference, test, samples, tolerance):
    """
    Compare reference and test reports. Will work for both relative abundance and read counts.

    Returns:
    - missing_species
    - new_species
    - abundance_differences
    """
    missing_species = sorted(set(reference) - set(test))
    new_species = sorted(set(test) - set(reference))

    abundance_differences = []

    for species in reference:
        if species not in test:
            continue

        for sample in samples:
            ref_val = reference[species].get(sample, 0.0)
            test_val = test[species].get(sample, 0.0)
            # If the ref_val is 0, then the limit will be 0. This is intended to make the user aware of new species.
            min_limit = ref_val * (1 - tolerance)
            max_limit = ref_val * (1 + tolerance)

            if not min_limit <= test_val <= max_limit:
                change = test_val / ref_val - 1 if ref_val != 0.0 else "none"
                abundance_differences.append(
                    (
                        species,
                        sample,
                        ref_val,
                        test_val,
                        change,
                    )
                )

    return missing_species, new_species, abundance_differences


def write_results(
    outdir,
    missing_species,
    new_species,
    abundance_differences,
    version,
    tolerance,
):
    os.makedirs(outdir, exist_ok=True)

    log_path = os.path.join(outdir, "verification.log")
    diff_path = os.path.join(outdir, "abundance_differences.tsv")

    with open(log_path, "w") as log:
        log.write("VERIFICATION SUMMARY\n")
        log.write(f"vec.py version {version}\n")
        log.write(f"tolerance level {tolerance}\n")
        log.write("====================\n\n")

        log.write(f"Missing species: {len(missing_species)}\n")
        for s in missing_species:
            log.write(f"  - {s}\n")

        log.write(f"\nNew species: {len(new_species)}\n")
        for s in new_species:
            log.write(f"  + {s}\n")

        log.write(f"\nAbundance differences: {len(abundance_differences)}\n")

    with open(diff_path, "w", newline="") as out:
        writer = csv.writer(out, delimiter="\t")
        writer.writerow(
            [
                "species",
                "sample",
                "reference_abundance",
                "test_abundance",
                "percentage difference",
            ]
        )

        for row in abundance_differences:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        description="Verify species and abundance against a reference report. This tool is designed to compare reports from emu combine-outputs."
    )

    parser.add_argument(
        "--reference",
        required=True,
        help="Reference report file (correct report).",
    )
    parser.add_argument(
        "--test",
        required=True,
        help="New report file to verify. This should be the report file which is produced by emu combine-outputs",
    )
    parser.add_argument(
        "--outdir",
        required=True,
        help="""Output directory for verification results.
             Note that the percentage difference results will differ slightly for relative abundance vs read count.
             Results genereated from relative abundance should be compared to results that were also generated from relative abundance data.
             Results coming from read count data should be compared to results that were also generated from read count data.
             """,
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.00001,
        metavar="[0-1]",
        help="Allowed fractional difference in abundance (e.g., 0.01 = 1%%).",
    )
    __version__ = "1.0.0"
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )

    args = parser.parse_args()
    if not (0.0 <= args.tolerance <= 1.0):
        parser.error("--tolerance must be between 0.0 and 1.0")

    samples_ref, ref_data = read_report(args.reference)
    samples_test, test_data = read_report(args.test)

    if samples_ref != samples_test:
         raise ValueError("Sample columns do not match between reports")

    missing, new, diffs = compare_reports(
        ref_data,
        test_data,
        samples_ref,
        tolerance=args.tolerance,
    )

    write_results(args.outdir, missing, new, diffs, __version__,args.tolerance)

    print("Verification complete")
    print(f"Results written to: {args.outdir}")


if __name__ == "__main__":
    main()
