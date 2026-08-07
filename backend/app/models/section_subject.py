from sqlalchemy import Column, Integer, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SectionSubject(BaseModel):
    __tablename__ = "section_subjects"

    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    
    lecture_slots_needed = Column(Integer, default=3, nullable=False)
    tutorial_slots_needed = Column(Integer, default=0, nullable=False)
    lab_slots_needed = Column(Integer, default=0, nullable=False)
    
    lecture_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True, index=True)
    tutorial_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True, index=True)
    lab_lead_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True, index=True)
    lab_co_faculty_ids = Column(JSON, nullable=True)  # List[int] of co-faculty IDs
    
    lab_consecutive_override = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('section_id', 'subject_id', name='uq_section_subject'),
    )

    section = relationship("Section", back_populates="section_subjects")
    subject = relationship("Subject", back_populates="section_subjects")
    lecture_faculty = relationship("Faculty", foreign_keys=[lecture_faculty_id], back_populates="section_subjects_lecture")
    tutorial_faculty = relationship("Faculty", foreign_keys=[tutorial_faculty_id], back_populates="section_subjects_tutorial")
    lab_lead_faculty = relationship("Faculty", foreign_keys=[lab_lead_faculty_id], back_populates="section_subjects_lab_lead")
