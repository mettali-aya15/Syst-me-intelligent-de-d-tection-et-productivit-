import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

export function exportRapportPDF(data: any) {
  const doc = new jsPDF();

  doc.setFontSize(16);
  doc.text('Rapport Global Usine', 14, 15);
autoTable(doc, {
  startY: 25,
  head: [['Nom', 'Email', 'Poste', 'Département', 'Performance']],
  body: data.employees.map((e: any) => [
    `${e.firstName} ${e.lastName}`,
    e.email,
    e.position,
    e.department,
    e.performance + '%'
  ])
});doc.addPage();
doc.text('Machines', 14, 15);

autoTable(doc, {
  startY: 25,
  head: [['Nom', 'Type', 'Statut', 'Efficacité']],
  body: data.machines.map((m: any) => [
    m.name,
    m.type,
    m.status,
    m.efficiency + '%'
  ])
});
doc.addPage();
doc.text('Production', 14, 15);

autoTable(doc, {
  startY: 25,
  head: [['Date', 'Machine', 'Produit', 'Quantité', 'Efficacité']],
  body: data.production.map((p: any) => [
    p.date,
    p.machineId,
    p.product,
    `${p.actualQuantity}/${p.targetQuantity}`,
    p.efficiency + '%'
  ])
});

  autoTable(doc, {
    startY: 25,
    head: [['Section', 'Nombre']],
    body: [
      ['Employés', data.employees.length],
      ['Machines', data.machines.length],
      ['Productions', data.production.length],
      ['KPIs', data.kpis.length]
    ]
  });

  doc.addPage();
  doc.text('KPIs', 14, 15);

  autoTable(doc, {
    startY: 25,
    head: [['Nom', 'Valeur', 'Objectif']],
    body: data.kpis.map((k: any) => [
      k.name,
      `${k.value} ${k.unit}`,
      k.target
    ])
  });

  doc.save('rapport-usine.pdf');
  doc.addPage();
doc.text('Employés', 14, 15);



}
