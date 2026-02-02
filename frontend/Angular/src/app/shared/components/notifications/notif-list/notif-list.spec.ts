import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NotifList } from './notif-list';

describe('NotifList', () => {
  let component: NotifList;
  let fixture: ComponentFixture<NotifList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NotifList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NotifList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
