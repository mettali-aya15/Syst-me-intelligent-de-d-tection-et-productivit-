import { TestBed } from '@angular/core/testing';

import { ExpPdf } from './exp-pdf';

describe('ExpPdf', () => {
  let service: ExpPdf;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ExpPdf);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
