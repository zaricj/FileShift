import re

# Load the log file content
log_content = r"""
28.06.24 08:04:22	Marking file './lib/scriptella-uber-1.4.4.jar' to be deleted on exit of JVM
28.06.24 08:04:22	Could not delete file. .\lib\xmlunit-core-2.9.0.jar: Der Prozess kann nicht auf die Datei zugreifen, da sie von einem anderen Prozess verwendet wird.
28.06.24 08:04:22	Marking file './lib/xmlunit-core-2.9.0.jar' to be deleted on exit of JVM
28.06.24 08:04:22	Could not delete file. .\lib\xmlunit-matchers-2.9.0.jar: Der Prozess kann nicht auf die Datei zugreifen, da sie von einem anderen Prozess verwendet wird.
28.06.24 08:04:22	Marking file './lib/xmlunit-matchers-2.9.0.jar' to be deleted on exit of JVM
28.06.24 08:04:22	Patch folder was cleared.
28.06.24 08:04:22	Validating installed libraries... please wait
07.01.25 13:12:23	Marking file './lib/mongodb-driver-core-4.10.2.jar' to be deleted on exit of JVM
07.01.25 13:12:23	Could not delete file. .\lib\mongodb-driver-sync-4.10.2.jar: Der Prozess kann nicht auf die Datei zugreifen, da sie von einem anderen Prozess verwendet wird.
07.01.25 13:12:23	Marking file './lib/mongodb-driver-sync-4.10.2.jar' to be deleted on exit of JVM
07.01.25 13:12:23	Could not delete file. .\lib\scriptella-uber-1.4.5.jar: Der Prozess kann nicht auf die Datei zugreifen, da sie von einem anderen Prozess verwendet wird.
07.01.25 13:12:23	Marking file './lib/scriptella-uber-1.4.5.jar' to be deleted on exit of JVM
07.01.25 13:12:23	Patch folder was cleared.
07.01.25 13:12:23	Validating installed libraries... please wait
"""

# Extract unique dates from the log
date_pattern = r"(\d{2}\.\d{2}\.\d{2})"
dates = sorted(set(re.findall(date_pattern, log_content)))

# Display the available dates
print("Available dates:")
for i, date in enumerate(dates, start=1):
    print(f"{i}. {date}")

# Ask the user to select a date
selected_index = int(input("\nSelect a date by number: ")) - 1
selected_date = dates[selected_index]

# Filter lines by the selected date
filtered_lines = [
    line for line in log_content.splitlines() if line.startswith(selected_date)
]

# Display the filtered lines
print(f"\nLog entries for {selected_date}:")
for line in filtered_lines:
    print(line)
