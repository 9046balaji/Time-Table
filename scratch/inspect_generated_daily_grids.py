import openpyxl

wb = openpyxl.load_workbook(r"c:\Users\ggvfj\Downloads\All Projects\Time_Table\time_table\VFSTR_ACSE_TIMETABLE_GENERATED_20260813_192621.xlsx", data_only=True)



def print_sheet_grid(sname):
    sheet = wb[sname]
    print(f"==================================================================================")
    print(f"   FRESH GENERATED GRID FOR SECTION: {sname}")
    print(f"==================================================================================")
    for r in range(7, 13):
        row_vals = [sheet.cell(r, c).value for c in range(1, 12)]
        day = row_vals[0]
        p1, p2, p3, p4, p5, p6, p7, p8 = (
            row_vals[1], row_vals[2], row_vals[4], row_vals[5],
            row_vals[6], row_vals[8], row_vals[9], row_vals[10]
        )
        def clean(val):
            if not val:
                return "---"
            return str(val).splitlines()[0][:12]

        print(f"  {day:<4} | P1:{clean(p1):<12} | P2:{clean(p2):<12} | P3:{clean(p3):<12} | P4:{clean(p4):<12} | P5:{clean(p5):<12} | P6:{clean(p6):<12} | P7:{clean(p7):<12} | P8:{clean(p8):<12}")

print_sheet_grid("II AIML-A")
print()
print_sheet_grid("III AIML-A")
