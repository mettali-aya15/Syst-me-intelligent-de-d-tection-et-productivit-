import { TestBed } from '@angular/core/testing';

import { UserMangmnt } from './user-mangmnt';

describe('UserMangmnt', () => {
  let service: UserMangmnt;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(UserMangmnt);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
