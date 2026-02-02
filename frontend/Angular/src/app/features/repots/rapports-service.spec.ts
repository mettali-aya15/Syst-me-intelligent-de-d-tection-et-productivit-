import { TestBed } from '@angular/core/testing';

import { RapportsService } from './rapports-service';

describe('RapportsService', () => {
  let service: RapportsService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(RapportsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
