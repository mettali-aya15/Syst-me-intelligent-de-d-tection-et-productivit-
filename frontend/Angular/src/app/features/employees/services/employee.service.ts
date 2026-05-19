import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface Employee {
  id?: string;
  _id?: string;
  name: string;
  full_name: string;
  email?: string;
  department?: string;
  photo_url?: string;
  active: boolean;
  created_at?: Date;
  updated_at?: Date;
}

@Injectable({
  providedIn: 'root'
})
export class EmployeeService {
  private readonly API_URL = `${environment.apiUrl}/api/v1`;
  private http = inject(HttpClient);

  getEmployees(activeOnly: boolean = true): Observable<Employee[]> {
    return this.http.get<Employee[]>(`${this.API_URL}/employees/?active_only=${activeOnly}`);
  }

  getEmployee(id: string): Observable<Employee> {
    return this.http.get<Employee>(`${this.API_URL}/employees/${id}`);
  }

  createEmployee(employee: Partial<Employee>): Observable<Employee> {
    return this.http.post<Employee>(`${this.API_URL}/employees/`, employee);
  }

  updateEmployee(id: string, employee: Partial<Employee>): Observable<Employee> {
    return this.http.put<Employee>(`${this.API_URL}/employees/${id}`, employee);
  }

  deleteEmployee(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/employees/${id}`);
  }
}