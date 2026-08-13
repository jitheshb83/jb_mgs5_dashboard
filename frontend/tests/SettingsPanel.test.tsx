import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SettingsPanel } from "../src/components/SettingsPanel";
import { mockSettings } from "../src/hooks/mockData";

describe("SettingsPanel", () => {
  it("blocks submission and shows a visible error when interval < min gap", () => {
    const onSave = vi.fn().mockResolvedValue(mockSettings);
    render(<SettingsPanel settings={mockSettings} isSaving={false} onSave={onSave} />);

    const intervalInput = screen.getByLabelText(/schedule interval/i) as HTMLInputElement;
    // mockSettings.min_refresh_gap_minutes is 30, so 10 is invalid.
    fireEvent.change(intervalInput, { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: /save settings/i }));

    expect(screen.getByRole("alert").textContent).toMatch(/must be at least/i);
    expect(onSave).not.toHaveBeenCalled();
  });

  it("submits when interval >= min gap", () => {
    const onSave = vi.fn().mockResolvedValue(mockSettings);
    render(<SettingsPanel settings={mockSettings} isSaving={false} onSave={onSave} />);

    fireEvent.click(screen.getByRole("button", { name: /save settings/i }));

    expect(onSave).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("picks up settings that arrive after mount (e.g. the async GET /api/settings load)", () => {
    const fallback = { ...mockSettings, battery_nameplate_kwh: 62.1 };
    const onSave = vi.fn().mockResolvedValue(mockSettings);
    const { rerender } = render(<SettingsPanel settings={fallback} isSaving={false} onSave={onSave} />);

    const capacityInput = screen.getByLabelText(/battery nameplate capacity/i) as HTMLInputElement;
    expect(capacityInput.value).toBe("62.1");

    // GET /api/settings resolves with the vehicle's real value, arriving after mount.
    const loaded = { ...mockSettings, battery_nameplate_kwh: 64.0 };
    rerender(<SettingsPanel settings={loaded} isSaving={false} onSave={onSave} />);

    expect(capacityInput.value).toBe("64");

    fireEvent.click(screen.getByRole("button", { name: /save settings/i }));
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ battery_nameplate_kwh: 64 }));
  });
});
