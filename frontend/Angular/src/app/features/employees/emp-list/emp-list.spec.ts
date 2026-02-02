import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EmpList } from './emp-list';

describe('EmpList', () => {
  let component: EmpList;
  let fixture: ComponentFixture<EmpList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EmpList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(EmpList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
