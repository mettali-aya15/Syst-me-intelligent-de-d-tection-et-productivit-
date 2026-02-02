import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

export function exportRapportExcel(data: any) {
  const workbook = XLSX.utils.book_new();

  const sheets = [
    { name: 'Employees', data: data.employees },
    { name: 'Machines', data: data.machines },
    { name: 'Production', data: data.production },
    { name: 'KPIs', data: data.kpis }
  ];

  sheets.forEach(sheet => {
    const ws = XLSX.utils.json_to_sheet(sheet.data);
    XLSX.utils.book_append_sheet(workbook, ws, sheet.name);
  });

  const buffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
  saveAs(new Blob([buffer]), 'rapport-usine.xlsx');
}
