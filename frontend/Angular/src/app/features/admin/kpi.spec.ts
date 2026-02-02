import { TestBed } from '@angular/core/testing';

import {  KpiService } from './kpi';

describe('Kpi', () => {
  let service: KpiService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(KpiService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
