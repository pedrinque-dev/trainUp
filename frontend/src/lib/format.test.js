import { describe, expect, it } from "vitest";
import { addDays, dayLong, dayShort, initials, mondayOf, num, weekdayIndex, zonedToUtc } from "./format";

describe("datas civis (sem fuso)", () => {
  it("formata dd/mm e dd/mm/aaaa", () => {
    expect(dayShort("2026-10-18")).toBe("18/10");
    expect(dayLong("2026-10-18")).toBe("18/10/2026");
  });
  it("soma dias atravessando mês e ano", () => {
    expect(addDays("2026-12-30", 3)).toBe("2027-01-02");
    expect(addDays("2026-03-01", -1)).toBe("2026-02-28");
  });
  it("semana começa na segunda", () => {
    expect(weekdayIndex("2026-10-19")).toBe(0); // segunda
    expect(weekdayIndex("2026-10-18")).toBe(6); // domingo
    expect(mondayOf("2026-10-18")).toBe("2026-10-12");
  });
});

describe("fuso America/Sao_Paulo", () => {
  it("converte horário digitado em Brasília para UTC (UTC-3)", () => {
    expect(zonedToUtc("2026-10-18T10:00")).toBe("2026-10-18T13:00:00.000Z");
    expect(zonedToUtc("2026-10-18T23:30")).toBe("2026-10-19T02:30:00.000Z");
  });
});

describe("helpers", () => {
  it("iniciais e números pt-BR", () => {
    expect(initials("Ana Clara Souza")).toBe("AC");
    expect(num(1234.56)).toBe("1.234,6");
    expect(num(null)).toBe("0");
  });
});
