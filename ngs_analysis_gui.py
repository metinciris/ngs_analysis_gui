import pandas as pd
from tkinter import Tk, filedialog
from tkinter import messagebox
import os

def ensure_numeric_and_string(df, chromosome_column, position_column):
    """Ensure chromosome is string and position is numeric."""
    df.iloc[:, chromosome_column - 1] = df.iloc[:, chromosome_column - 1].astype(str)
    df.iloc[:, position_column - 1] = pd.to_numeric(df.iloc[:, position_column - 1], errors="coerce")
    return df

def analyze_files(file_paths, allele_fraction_column=22, chromosome_column=1, position_column=2, threshold=0.1):
    """Perform contamination analysis on selected files."""
    dataframes = {os.path.basename(path): pd.read_csv(path) for path in file_paths}
    
    # Ensure data consistency
    for file_name, df in dataframes.items():
        dataframes[file_name] = ensure_numeric_and_string(df, chromosome_column, position_column)

    results = []
    file_names = list(dataframes.keys())

    for i in range(len(file_names)):
        for j in range(i + 1, len(file_names)):
            file_1_name = file_names[i]
            file_2_name = file_names[j]

            df1 = dataframes[file_1_name]
            df2 = dataframes[file_2_name]

            df1_high_quality = df1[df1.iloc[:, allele_fraction_column - 1] >= threshold]
            df2_high_quality = df2[df2.iloc[:, allele_fraction_column - 1] >= threshold]

            shared_mutations = pd.merge(
                df1_high_quality.iloc[:, [chromosome_column - 1, position_column - 1, allele_fraction_column - 1]],
                df2_high_quality.iloc[:, [chromosome_column - 1, position_column - 1, allele_fraction_column - 1]],
                on=[df1.columns[chromosome_column - 1], df1.columns[position_column - 1]],
                suffixes=('_File1', '_File2')
            )

            unique_to_file1 = len(df1_high_quality) - len(shared_mutations)
            unique_to_file2 = len(df2_high_quality) - len(shared_mutations)

            unique_to_file1 = max(unique_to_file1, 0)
            unique_to_file2 = max(unique_to_file2, 0)

            avg_file1_fraction = shared_mutations.iloc[:, -2].mean()
            avg_file2_fraction = shared_mutations.iloc[:, -1].mean()

            contamination_percentage_file1_to_file2 = int(round((avg_file1_fraction / (avg_file1_fraction + avg_file2_fraction)) * 100)) if avg_file1_fraction + avg_file2_fraction > 0 else 0
            contamination_percentage_file2_to_file1 = int(round((avg_file2_fraction / (avg_file1_fraction + avg_file2_fraction)) * 100)) if avg_file1_fraction + avg_file2_fraction > 0 else 0

            results.append({
                "Primary Source": file_1_name if avg_file1_fraction > avg_file2_fraction else file_2_name,
                "File 1": file_1_name,
                "File 2": file_2_name,
                "Shared Mutations": len(shared_mutations),
                "Unique to File 1": unique_to_file1,
                "Unique to File 2": unique_to_file2,
                "Contamination % (File 1 to File 2)": contamination_percentage_file1_to_file2,
                "Contamination % (File 2 to File 1)": contamination_percentage_file2_to_file1,
            })

    return pd.DataFrame(results)

def main():
    root = Tk()
    root.withdraw()
    
    messagebox.showinfo("File Selection", "Please select the CSV files for analysis.")
    file_paths = filedialog.askopenfilenames(filetypes=[("CSV files", "*.csv")])

    if not file_paths:
        messagebox.showerror("Error", "No files selected. Exiting.")
        return

    try:
        results = analyze_files(file_paths)
        output_file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save Results")

        if output_file:
            results.to_csv(output_file, index=False)
            messagebox.showinfo("Success", f"Results saved to {output_file}\n\nNote: Results are representative and may include shared sequencing errors.")
        else:
            messagebox.showinfo("Cancelled", "Results not saved.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
