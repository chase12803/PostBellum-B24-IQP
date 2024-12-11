import pandas as pd
import ast  # To safely evaluate string representations of lists
import tkinter as tk
from tkinter import Text, filedialog, messagebox


class BiographyLabeler:
    def __init__(self, root, dataframe):
        self.root = root
        self.df = dataframe
        self.current_index = 0

        # Ensure lists are properly parsed from strings
        self.df['past_countries'] = self.df['past_countries'].apply(self.parse_list)
        self.df['present_countries'] = self.df['present_countries'].apply(self.parse_list)
        self.df['czech_regions'] = self.df['czech_regions'].apply(self.parse_list)

        # Predefined options
        self.past_countries_options = ["Czechoslovakia", "Nazi territories", "Soviet territories"]
        self.present_countries_options = ["Czechia", "Slovakia"]
        self.czech_regions_options = [
            "Hlavní město Praha", "Středočeský kraj", "Jihočeský kraj", "Plzeňský kraj",
            "Karlovarský kraj", "Ústecký kraj", "Liberecký kraj", "Královéhradecký kraj",
            "Pardubický kraj", "Kraj Vysočina", "Jihomoravský kraj", "Olomoucký kraj",
            "Moravskoslezský kraj", "Zlínský kraj"
        ]

        # Title and Geometry
        self.root.title("Biography Labeling Tool")
        self.root.geometry("1200x800")

        # Biography Display
        self.bio_label = tk.Label(self.root, text="Biography:", font=("Helvetica", 14))
        self.bio_label.pack(pady=10)

        self.bio_text = Text(self.root, wrap=tk.WORD, height=10, font=("Helvetica", 12))  # Reduced height
        self.bio_text.pack(pady=10, fill=tk.BOTH)
        self.bio_text.config(state=tk.DISABLED)

        # Navigation Buttons
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(pady=10)

        self.prev_button = tk.Button(nav_frame, text="Previous", command=self.previous_bio, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(nav_frame, text="Next", command=self.next_bio)
        self.next_button.pack(side=tk.LEFT, padx=5)

        # Jump to Index
        jump_frame = tk.Frame(self.root)
        jump_frame.pack(pady=10)

        tk.Label(jump_frame, text="Jump to Index:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.jump_entry = tk.Entry(jump_frame, width=10, font=("Helvetica", 12))
        self.jump_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(jump_frame, text="Go", command=self.jump_to_index, font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)


        # Labeling Buttons
        label_frame = tk.Frame(self.root)
        label_frame.pack(side=tk.RIGHT, padx=10, fill=tk.Y)

        # Past Countries Buttons and Text Box
        self.create_button_column(label_frame, "Past Countries", self.past_countries_options, "past_countries", 0)
        self.add_text_input(label_frame, "past_countries", self.past_countries_options, 0)

        # Present Countries Buttons and Text Box
        self.create_button_column(label_frame, "Present Countries", self.present_countries_options, "present_countries", 1)
        self.add_text_input(label_frame, "present_countries", self.present_countries_options, 1)

        # Czech Regions Buttons
        self.create_button_column(label_frame, "Czech Regions", self.czech_regions_options, "czech_regions", 2)

        # Current Selections Display
        self.current_selections = Text(self.root, wrap=tk.WORD, height=8, font=("Helvetica", 12))
        self.current_selections.pack(pady=10, fill=tk.BOTH)
        self.current_selections.config(state=tk.DISABLED)

        # Save Button
        save_button = tk.Button(self.root, text="Save to CSV", command=self.save_to_csv, font=("Helvetica", 12))
        save_button.pack(pady=10)

        # Load the first biography
        self.display_biography()

    def parse_list(self, value):
        """Safely parse a string representation of a list."""
        if isinstance(value, str):
            try:
                return ast.literal_eval(value) if value.startswith("[") and value.endswith("]") else []
            except (ValueError, SyntaxError):
                return []
        return value if isinstance(value, list) else []

    def create_button_column(self, parent, label, options, column_name, col_index):
        tk.Label(parent, text=label, font=("Helvetica", 12)).grid(row=0, column=col_index, padx=5, pady=5)
        for i, option in enumerate(options):
            tk.Button(
                parent, 
                text=option, 
                command=lambda opt=option: self.toggle_selection(column_name, opt)
            ).grid(row=i + 1, column=col_index, padx=5, pady=5)

        # Add "Remove Custom Countries" button
        tk.Button(
            parent,
            text="Remove Custom Countries",
            command=lambda: self.remove_custom_countries(column_name, options),
            font=("Helvetica", 10)
        ).grid(row=len(options) + 2, column=col_index, padx=5, pady=5)

    def add_text_input(self, parent, column_name, predefined_options, col_index):
        # Text input field and add button
        text_entry = tk.Entry(parent, font=("Helvetica", 10), width=20)
        text_entry.grid(row=100, column=col_index, padx=5, pady=5)
        tk.Button(
            parent, 
            text="Add", 
            command=lambda: self.add_to_list(column_name, text_entry.get())
        ).grid(row=101, column=col_index, padx=5, pady=5)

    def display_biography(self):
        # Clear existing text
        self.bio_text.config(state=tk.NORMAL)
        self.bio_text.delete("1.0", tk.END)

        # Insert current biography text
        biography = self.df.loc[self.current_index, "field_biography_value"]
        self.bio_text.insert(tk.END, biography)
        self.bio_text.config(state=tk.DISABLED)

        # Update selections display
        self.display_current_selections()

        # Update navigation button states
        self.update_buttons()

    def display_current_selections(self):
        self.current_selections.config(state=tk.NORMAL)
        self.current_selections.delete("1.0", tk.END)

        # Get current selections for each column
        past = ", ".join(self.df.loc[self.current_index, "past_countries"])
        present = ", ".join(self.df.loc[self.current_index, "present_countries"])
        regions = ", ".join(self.df.loc[self.current_index, "czech_regions"])

        # Display them in the text widget
        self.current_selections.insert(tk.END, f"Index: {self.current_index}\n")
        self.current_selections.insert(tk.END, f"Past Countries: {past}\n")
        self.current_selections.insert(tk.END, f"Present Countries: {present}\n")
        self.current_selections.insert(tk.END, f"Czech Regions: {regions}")
        self.current_selections.config(state=tk.DISABLED)

    def update_buttons(self):
        # Disable 'Previous' button if at the first entry
        self.prev_button.config(state=tk.DISABLED if self.current_index == 0 else tk.NORMAL)
        # Disable 'Next' button if at the last entry
        self.next_button.config(state=tk.DISABLED if self.current_index == len(self.df) - 1 else tk.NORMAL)

    def previous_bio(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.display_biography()

    def next_bio(self):
        if self.current_index < len(self.df) - 1:
            self.current_index += 1
            self.display_biography()

    def add_to_list(self, column_name, value):
        if value and value not in self.df.at[self.current_index, column_name]:
            self.df.at[self.current_index, column_name].append(value)
            self.display_current_selections()

    def toggle_selection(self, column_name, value):
        current_list = self.df.at[self.current_index, column_name]
        if value in current_list:
            current_list.remove(value)
        else:
            current_list.append(value)
        self.display_current_selections()

    def remove_custom_countries(self, column_name, predefined_options):
        current_list = self.df.at[self.current_index, column_name]
        self.df.at[self.current_index, column_name] = [
            item for item in current_list if item in predefined_options
        ]
        self.display_current_selections()

    def jump_to_index(self):
        try:
            # Get index from entry field
            index = int(self.jump_entry.get())
            if 0 <= index < len(self.df):
                self.current_index = index
                self.display_biography()
            else:
                messagebox.showerror("Error", f"Index out of range. Please enter a value between 0 and {len(self.df) - 1}.")
        except ValueError:
            messagebox.showerror("Error", "Invalid index. Please enter a numeric value.")
            
    def save_to_csv(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path:
            # Save lists as strings
            self.df.to_csv(save_path, index=False)
            messagebox.showinfo("Save Successful", f"Dataframe saved to {save_path}")
            


# Load CSV file
file_path = filedialog.askopenfilename(title="Open CSV File", filetypes=[("CSV files", "*.csv")])
if file_path:
    df = pd.read_csv(file_path)

    if "field_biography_value" in df.columns:
        # Initialize GUI
        root = tk.Tk()
        app = BiographyLabeler(root, df)
        root.mainloop()
    else:
        print("The column 'field_biography_value' was not found in the CSV file.")
else:
    print("No file selected.")
