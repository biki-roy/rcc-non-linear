import win32com.client as win32
def get_excel_file_path(workbook_name=None):
    """Return the filesystem path of the named workbook that is already open in Excel."""

    excel = win32.GetActiveObject("Excel.Application")

    if workbook_name:
        try:
            wb = excel.Workbooks(workbook_name)
        except Exception as e:
            raise ValueError(f"Workbook '{workbook_name}' not found: {e}")
    else:
        wb = excel.ActiveWorkbook

    if wb is None:
        raise ValueError("No active workbook found.")

    # If workbook has never been saved
    if wb.Path == "":
        raise ValueError("Workbook has not been saved to disk.")

    return wb.FullName  # Absolute path