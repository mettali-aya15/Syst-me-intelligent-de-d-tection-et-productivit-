// src/app/core/services/employee.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';

export interface Employee {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  position: string;
  department: string;
  shift: string;
  status: 'active' | 'inactive';
  hireDate?: string;
  performance: number;
  avatar: string;
  role?: string;
}

@Injectable({
  providedIn: 'root'
})
export class EmployeeService {
  private readonly API_URL = 'http://localhost:3000/api';
  private http = inject(HttpClient);

  private employeesSubject = new BehaviorSubject<Employee[]>([]);
  public employees$ = this.employeesSubject.asObservable();



  
  getEmployees(): Observable<Employee[]> {
    return this.http.get<Employee[]>(`${this.API_URL}/employees`)
      .pipe(
        tap(employees => {
          this.employeesSubject.next(employees);
          console.log('✅ Employés chargés:', employees.length);
        })
      );
  }

  getEmployee(id: string): Observable<Employee> {
    return this.http.get<Employee>(`${this.API_URL}/employees/${id}`);
  }

  createEmployee(employee: Omit<Employee, 'id'>): Observable<Employee> {
    return this.http.post<Employee>(`${this.API_URL}/employees`, {
      ...employee,
      id: 'emp_' + Date.now()
    }).pipe(
      tap(() => this.getEmployees().subscribe())
    );
  }

  updateEmployee(id: string, data: Partial<Employee>): Observable<Employee> {
    return this.http.patch<Employee>(`${this.API_URL}/employees/${id}`, data)
      .pipe(
        tap(() => this.getEmployees().subscribe())
      );
  }

  deleteEmployee(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/employees/${id}`)
      .pipe(
        tap(() => this.getEmployees().subscribe())
      );
  }


}