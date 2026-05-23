"use client";

import { useState } from "react";
import type { DateBounds } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type DateRangePickerProps = {
  bounds: DateBounds;
  startDate: string;
  endDate: string;
  onApply: (range: { startDate: string; endDate: string }) => void;
};

export function DateRangePicker({
  bounds,
  startDate,
  endDate,
  onApply,
}: DateRangePickerProps) {
  const [draftStartDate, setDraftStartDate] = useState(startDate);
  const [draftEndDate, setDraftEndDate] = useState(endDate);

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-[var(--surface-subdued)] p-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase text-muted-foreground">
            Start date
          </label>
          <Input
            type="date"
            min={bounds.min_date}
            max={bounds.max_date}
            value={draftStartDate}
            onChange={(event) => setDraftStartDate(event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase text-muted-foreground">
            End date
          </label>
          <Input
            type="date"
            min={bounds.min_date}
            max={bounds.max_date}
            value={draftEndDate}
            onChange={(event) => setDraftEndDate(event.target.value)}
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          onClick={() =>
            onApply({
              startDate: draftStartDate,
              endDate: draftEndDate,
            })
          }
        >
          Apply dates
        </Button>
        <Button
          variant="outline"
          onClick={() =>
            onApply({
              startDate: bounds.default_start_date,
              endDate: bounds.default_end_date,
            })
          }
        >
          Latest 30 days
        </Button>
      </div>
    </div>
  );
}
