import { TestBed } from '@angular/core/testing';

import { ExpExcel } from './exp-excel';

describe('ExpExcel', () => {
  let service: ExpExcel;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ExpExcel);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
