

import { Injectable, OnInit, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
export interface Machine {
  id: string;
  name: string;
  type: string;
  manufacturer: string;
  model: string;
  serialNumber: string;
  location: string;
  status: 'running' | 'stopped' | 'maintenance';
  efficiency: number;
  productionRate: number;
  lastMaintenance: string;
  nextMaintenance: string;
  operatorId: string | null;
}
@Injectable({
  providedIn: 'root',
})
export class MachineService  {
 




  private readonly API_URL = 'http://localhost:3000/api';
  private http = inject(HttpClient);

  private machinesSubject = new BehaviorSubject<Machine[]>([]);
  public machines$ = this.machinesSubject.asObservable();

  getMachines(): Observable<Machine[]> {
    return this.http.get<Machine[]>(`${this.API_URL}/machines`)
      .pipe(tap(machines => this.machinesSubject.next(machines)));
  }

  getMachine(id: string): Observable<Machine> {
    return this.http.get<Machine>(`${this.API_URL}/machines/${id}`);
  }

  createMachine(machine: Omit<Machine, 'id'>): Observable<Machine> {
    return this.http.post<Machine>(`${this.API_URL}/machines`, {
      ...machine,
      id: 'mach_' + Date.now()
    }).pipe(tap(() => this.getMachines().subscribe()));
  }

  updateMachine(id: string, updates: Partial<Machine>): Observable<Machine> {
    return this.http.patch<Machine>(`${this.API_URL}/machines/${id}`, updates)
      .pipe(tap(() => this.getMachines().subscribe()));
  }

  deleteMachine(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/machines/${id}`)
      .pipe(tap(() => this.getMachines().subscribe()));
  }





}
  

