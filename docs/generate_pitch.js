const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageBreak, LevelFormat
} = require('docx');
const fs = require('fs');

const BRAND_GREEN = "0D7A5F";
const BRAND_DARK  = "0B1929";
const HEADER_BG   = "122438";
const LIGHT_BG    = "EBF5F0";
const MID_BG      = "D1EDE5";

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160 },
    children: [new TextRun({ text, font: "Arial", size: 32, bold: true, color: BRAND_DARK })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 120 },
    children: [new TextRun({ text, font: "Arial", size: 26, bold: true, color: BRAND_GREEN })]
  });
}

function h3(text) {
  return new Paragraph({
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, font: "Arial", size: 22, bold: true, color: BRAND_DARK })]
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 22, color: "2D2D2D", ...opts })]
  });
}

function bullet(text, bold = false) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, font: "Arial", size: 21, bold, color: "2D2D2D" })]
  });
}

function spacer(before = 200) {
  return new Paragraph({ spacing: { before, after: 0 }, children: [new TextRun("")] });
}

function colorRow(cells, bg, bold = false) {
  return new TableRow({
    children: cells.map((text, i) => new TableCell({
      borders,
      width: { size: i === 0 ? 3000 : 6360 / (cells.length - 1), type: WidthType.DXA },
      shading: { fill: bg, type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 140, right: 140 },
      children: [new Paragraph({
        children: [new TextRun({ text, font: "Arial", size: 20, bold: bold || i === 0, color: i === 0 && bold ? "FFFFFF" : "2D2D2D" })]
      })]
    }))
  });
}

function makeTable(headers, rows, headerBg = BRAND_GREEN) {
  const colCount = headers.length;
  const totalWidth = 9360;
  const colWidth = Math.floor(totalWidth / colCount);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: Array(colCount).fill(colWidth),
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map(h => new TableCell({
          borders,
          width: { size: colWidth, type: WidthType.DXA },
          shading: { fill: headerBg, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 140, right: 140 },
          children: [new Paragraph({
            children: [new TextRun({ text: h, font: "Arial", size: 20, bold: true, color: "FFFFFF" })]
          })]
        }))
      }),
      ...rows.map((row, ri) => new TableRow({
        children: row.map((cell, ci) => new TableCell({
          borders,
          width: { size: colWidth, type: WidthType.DXA },
          shading: { fill: ri % 2 === 0 ? "FFFFFF" : LIGHT_BG, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 140, right: 140 },
          children: [new Paragraph({
            children: [new TextRun({ text: cell, font: "Arial", size: 20, color: "2D2D2D" })]
          })]
        }))
      }))
    ]
  });
}

// Cover block (text-based, no image dependency)
function coverBlock() {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 720, after: 200 },
      children: [new TextRun({ text: "⚡ ChargeKaru", font: "Arial", size: 64, bold: true, color: BRAND_GREEN })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 160 },
      children: [new TextRun({ text: "Smart Seat-Charging System for KSRTC Buses", font: "Arial", size: 32, bold: false, color: BRAND_DARK })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 80, after: 80 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND_GREEN, space: 1 } },
      children: [new TextRun({ text: "", font: "Arial", size: 24 })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 80 },
      children: [new TextRun({ text: "Innovation Project Proposal", font: "Arial", size: 24, italics: true, color: "555555" })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 40, after: 1440 },
      children: [new TextRun({ text: "Karnataka State Road Transport Corporation (KSRTC) · Smart Transport Division", font: "Arial", size: 20, color: "888888" })]
    }),
  ];
}

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } }
      }]
    }]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: BRAND_DARK },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: BRAND_GREEN },
        paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    children: [
      ...coverBlock(),

      // ─── 1. Problem ───
      h1("1. Problem Statement"),
      body("Every day, lakhs of passengers travel on KSRTC and private buses across Karnataka — journeys that can last 2 to 8 hours. A significant number of these passengers board without a charged phone, or forget their charging cables and power banks at home. Once on the bus, there is no way to charge their device."),
      spacer(120),
      body("This creates real, measurable frustration:", { bold: true }),
      bullet("Passengers miss important calls, navigation, UPI payments, and entertainment during long journeys."),
      bullet("Bus operators have no differentiator — every bus looks the same to the passenger booking online."),
      bullet("KSRTC loses a simple revenue and loyalty opportunity to private operators who are beginning to add amenities."),
      spacer(120),
      body("A naive fix — just adding USB sockets — creates two new problems:", { bold: true }),
      bullet("Free-for-all usage: non-passengers can plug in at stops. Parked buses get drained overnight."),
      bullet("No accountability: if a socket malfunctions or overheats, there is no way to know which seat was affected."),
      spacer(80),

      // ─── 2. Solution ───
      h1("2. The ChargeKaru Solution"),
      body("ChargeKaru adds intelligence to the socket. Each seat has two inputs feeding into a controller:"),
      spacer(80),
      makeTable(
        ["Input", "What it detects", "Hardware component"],
        [
          ["Seat pressure sensor", "Whether a passenger is currently seated", "Conductive pressure mat under seat foam"],
          ["Ticket / pass scan", "Whether the seated person holds a valid KSRTC fare", "NFC reader or QR scanner at armrest"],
        ]
      ),
      spacer(160),
      body("The socket only goes live when both inputs are simultaneously true. The moment either drops — the passenger stands up, or their ticket is found invalid — power cuts off automatically."),
      spacer(120),
      body("Core activation rule (the entire business logic):", { bold: true }),
      new Paragraph({
        spacing: { before: 120, after: 120 },
        shading: { fill: "F0F4F8", type: ShadingType.CLEAR },
        children: [
          new TextRun({ text: "  IF  seat_pressure = TRUE  AND  ticket_valid = TRUE  →  socket ON", font: "Courier New", size: 20, color: "0A4D2E" }),
        ]
      }),
      new Paragraph({
        spacing: { before: 0, after: 160 },
        shading: { fill: "F0F4F8", type: ShadingType.CLEAR },
        children: [
          new TextRun({ text: "  ELSE  →  socket OFF  (always the safe default)", font: "Courier New", size: 20, color: "7A3020" }),
        ]
      }),

      // ─── 3. System Architecture ───
      h1("3. System Architecture"),
      body("ChargeKaru is a three-layer system — hardware at the seat, a backend server at the depot/cloud, and interfaces for conductors and passengers."),
      spacer(120),
      makeTable(
        ["Layer", "Component", "Technology"],
        [
          ["Seat hardware", "Pressure sensor + relay controller", "ESP32 microcontroller, MQTT"],
          ["Seat hardware", "Charging socket (USB-A + USB-C PD)", "5V/2A USB-A, 20W USB-C PD"],
          ["Seat hardware", "Ticket reader", "PN532 NFC module or QR scanner"],
          ["Backend", "Fleet management API", "Python FastAPI, REST + WebSocket"],
          ["Backend", "Ticket validation engine", "KSRTC reservation system integration"],
          ["Backend", "Energy monitoring", "Per-seat Wh tracking and alerting"],
          ["Conductor interface", "Fleet control dashboard", "Live seat map, validation override"],
          ["Passenger interface", "Charging status app", "Mobile web, no install required"],
        ]
      ),
      spacer(160),

      // ─── 4. Seat States ───
      h1("4. Seat States & Behaviour"),
      makeTable(
        ["State", "Condition", "Socket", "Indicator"],
        [
          ["Idle", "Seat empty", "OFF", "No light"],
          ["Occupied – unverified", "Passenger seated, no valid ticket", "OFF", "Amber LED"],
          ["Charging", "Passenger seated + ticket verified", "ON", "Green LED (pulse)"],
          ["Fault", "Sensor / relay error detected", "OFF", "Red LED"],
        ]
      ),
      spacer(160),

      // ─── 5. Key Features ───
      h1("5. Key Features"),
      h3("Dual-mode verification"),
      body("Supports both KSRTC printed tickets (QR code scan) and KSRTC Smart Pass / BMTC pass (NFC tap). The system validates against KSRTC's existing reservation database — no new card infrastructure required."),
      h3("Fleet-wide visibility"),
      body("The conductor's dashboard shows a live floor-plan of every bus in the depot — which seats are charging, which are occupied-unverified (passenger needs to show ticket), and total fleet power draw in real time."),
      h3("Auto-shutoff safety"),
      body("When a passenger stands up, the pressure sensor releases and power cuts within 200ms — before anyone at the next stop can reach the socket. This prevents unauthorised use at intermediate stops."),
      h3("Session energy logging"),
      body("Every charging session logs start time, seat ID, ticket/pass reference, and Wh consumed. This gives KSRTC real-world data to right-size battery packs and socket infrastructure per route."),
      h3("Conductor override"),
      body("If a passenger's NFC card is faulty, the conductor can manually verify via the dashboard (entering PNR or pass ID), unlocking the socket without requiring the passenger to use the app."),
      spacer(80),

      // ─── 6. Demo ───
      h1("6. Software Demo"),
      body("The project includes a fully working software simulation:"),
      spacer(80),
      makeTable(
        ["Component", "Description"],
        [
          ["FastAPI backend", "REST API simulating the fleet: buses, seats, sensor events, ticket validation"],
          ["Conductor dashboard", "Live fleet map (dashboard.html) — seat tiles light up green when charging, amber when unverified"],
          ["Passenger view", "Mobile-first web app (passenger.html) — select bus, enter seat, submit PNR, see charging status"],
          ["Journey simulator", "simulate_journey.py — auto-boards/exits passengers across the fleet for live presentation demos"],
        ]
      ),
      spacer(160),
      body("Quick start:", { bold: true }),
      new Paragraph({
        spacing: { before: 80, after: 60 },
        shading: { fill: "F0F4F8", type: ShadingType.CLEAR },
        children: [new TextRun({ text: "  cd backend && uvicorn app.main:app --reload --port 8000", font: "Courier New", size: 19, color: "1A1A1A" })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 60 },
        shading: { fill: "F0F4F8", type: ShadingType.CLEAR },
        children: [new TextRun({ text: "  python simulate_journey.py   # makes the fleet live", font: "Courier New", size: 19, color: "1A1A1A" })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 160 },
        shading: { fill: "F0F4F8", type: ShadingType.CLEAR },
        children: [new TextRun({ text: "  open frontend/dashboard.html in browser", font: "Courier New", size: 19, color: "1A1A1A" })]
      }),

      // ─── 7. Business Case ───
      h1("7. Business Case for KSRTC"),
      makeTable(
        ["Metric", "Estimate", "Basis"],
        [
          ["Buses in KSRTC fleet", "~8,500", "KSRTC Annual Report 2023–24"],
          ["Avg seats per bus", "36", "Standard KSRTC Express/Airavat"],
          ["Sockets per bus", "36", "One per seat"],
          ["Component cost per seat", "₹800 – ₹1,200", "ESP32 + relay + pressure mat + USB module"],
          ["Total hardware cost (pilot: 50 buses)", "₹15 – 22 lakh", "50 buses × 36 seats × ₹1,000"],
          ["Potential premium fare uplift", "₹20 – ₹50/ticket", "Passengers pay for amenities on VRL/SRS"],
          ["Break-even estimate", "~8 – 14 months", "On pilot fleet at 80% occupancy"],
        ]
      ),
      spacer(160),

      // ─── 8. Roadmap ───
      h1("8. Implementation Roadmap"),
      makeTable(
        ["Phase", "Milestone", "Timeline"],
        [
          ["Phase 1", "Software simulation + API (completed)", "Month 0"],
          ["Phase 2", "Hardware prototype — 1 bus, 36 seats", "Month 1–2"],
          ["Phase 3", "Integration with KSRTC ticketing API", "Month 2–3"],
          ["Phase 4", "Pilot fleet — 10 buses on Bengaluru–Mysuru route", "Month 3–5"],
          ["Phase 5", "Full fleet rollout + revenue model activation", "Month 6–12"],
        ]
      ),
      spacer(160),

      // ─── 9. Future Scope ───
      h1("9. Future Scope"),
      bullet("Revenue charging: First 30 minutes free per journey, ₹1–2/hour beyond that via UPI deep-link. Private operators (VRL, SRS) can adopt this as a paid amenity."),
      bullet("Solar integration: Supplement bus electrical draw with rooftop solar — especially useful for depot charging overnight."),
      bullet("ONDC / IRCTC extension: Same dual-sensor + ticket-lock approach works on trains, ferries, and airport buses."),
      bullet("Maintenance prediction: Vibration + temperature sensors at each seat module can flag failing hardware before it causes a passenger complaint."),
      bullet("Accessibility: Priority sockets (always-on at certain seats) for passengers with medical devices — flagged via accessibility pass type in KSRTC system."),
      spacer(200),

      // ─── 10. Team ───
      h1("10. Tech Stack Summary"),
      makeTable(
        ["Layer", "Technology"],
        [
          ["Backend API", "Python 3.11, FastAPI, Uvicorn, Pydantic v2"],
          ["Frontend", "React 18, Babel Standalone, vanilla CSS"],
          ["Hardware (real deploy)", "ESP32, MQTT broker, PN532 NFC, conductive pressure mat, USB PD relay"],
          ["Integration", "KSRTC Reservation API (REST), BMTC Smart Pass NFC"],
          ["Monitoring", "Per-seat energy logging, WebSocket live updates"],
        ]
      ),
      spacer(200),

      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 400 },
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: BRAND_GREEN, space: 1 } },
        children: [new TextRun({ text: "ChargeKaru — Charge smarter. Travel better.", font: "Arial", size: 22, italics: true, color: "555555" })]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/home/claude/chargekaru/docs/ChargeKaru_Pitch_Doc.docx', buf);
  console.log('ChargeKaru_Pitch_Doc.docx written successfully');
});
