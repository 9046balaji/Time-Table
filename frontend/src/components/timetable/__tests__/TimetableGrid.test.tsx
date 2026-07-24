import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TimetableGrid, SlotEntry } from '../TimetableGrid';

describe('TimetableGrid Component', () => {
  const sampleEntries: SlotEntry[] = [
    {
      id: '1',
      day: 'MON',
      period: 1,
      subjectCode: 'DS',
      roomCode: '601',
      facultyName: 'Dr. Reddy',
      subjectType: 'L',
    },
    {
      id: '2',
      day: 'WED',
      period: 1,
      subjectCode: 'OOPS(P)',
      roomCode: '606',
      facultyName: 'P. Girija',
      subjectType: 'P',
      hasClash: true,
      clashReason: 'Room 606 double-booked by III CS',
    },
  ];

  it('renders section title and days grid correctly', () => {
    render(<TimetableGrid sectionName="II AIML-A" entries={sampleEntries} />);
    
    expect(screen.getByText(/Timetable Matrix —/i)).toBeInTheDocument();
    expect(screen.getByText('II AIML-A')).toBeInTheDocument();
    expect(screen.getByText('MON')).toBeInTheDocument();
    expect(screen.getByText('WED')).toBeInTheDocument();
  });

  it('displays lecture and lab slot cells with proper badges', () => {
    render(<TimetableGrid sectionName="II AIML-A" entries={sampleEntries} />);
    
    expect(screen.getByText('DS')).toBeInTheDocument();
    expect(screen.getByText('601')).toBeInTheDocument();
    expect(screen.getByText('OOPS(P)')).toBeInTheDocument();
    expect(screen.getByText('606')).toBeInTheDocument();
  });

  it('triggers onCellClick when a slot cell is clicked', () => {
    const handleCellClick = vi.fn();
    render(
      <TimetableGrid
        sectionName="II AIML-A"
        entries={sampleEntries}
        onCellClick={handleCellClick}
      />
    );

    const lectureCell = screen.getByText('DS');
    fireEvent.click(lectureCell);

    expect(handleCellClick).toHaveBeenCalledTimes(1);
    expect(handleCellClick).toHaveBeenCalledWith(sampleEntries[0]);
  });
});
