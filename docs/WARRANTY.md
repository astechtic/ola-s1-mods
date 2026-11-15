# Warranty & "unofficial, not affiliated" — what it means

> **This is informational, not legal advice.** The decisive document is **your own warranty
> certificate / the version in the Ola app**, since coverage periods and wording vary by
> vehicle and change over time. Verify against the primary sources linked at the bottom.

S1Mods' disclaimer says: *"Modifying the scooter may void warranty — unofficial, not
affiliated with Ola."* Here is exactly what that is based on.

## 1. "Unofficial, not affiliated with Ola"

S1Mods is a **third‑party, community tool**. Ola Electric did not make, endorse, or support
it. *"Ola"* and *"MoveOS"* are trademarks of Ola Electric, used here only descriptively. If
something goes wrong, Ola support has no obligation to help with anything related to this tool,
and it will not recognise it.

## 2. "May void warranty" — grounded in Ola's own terms

This is **not** boilerplate. It maps directly to exclusions in Ola's published **Battery
Warranty Terms & Conditions**, Section 4:

| Clause | Verbatim exclusion |
| --- | --- |
| **6.8** | *"Control Units or software used in vehicle which are not designed or approved by the company"* (top‑up plans: *"Parts of software used in applications which were neither designed nor approved by the Company"*) |
| **6.7** | *"Modifications, alterations, tampering or improper repairs done at any unauthorized service points"* |
| (listed) | Not keeping **MoveOS up to date** can affect coverage |

S1Mods sideloads apps Ola didn't approve and enables diagnostic ADB — that falls squarely
under **6.8**, and arguably **6.7**. So *"may void warranty"* is an accurate, conservative
statement.

**Durations at stake** (per that page): the **battery** carries the long warranty (8‑year
tiers on the top‑up plans; standard battery/component terms are shorter), while **other
components, including the infotainment electronics, are ~36 months / 40,000 km**. A head‑unit
software mod most plausibly touches that second bucket — though Ola *could* invoke the software
exclusion more broadly.

## 3. The nuance: "may," not "will"

- **India has no clear equivalent of the US Magnuson‑Moss Warranty Act.** In the US, a maker
  generally must *prove the modification caused the specific failure* before denying a claim.
  No Indian statute or Consumer‑Forum ruling was found that firmly places that burden on the
  manufacturer for software mods. Some Indian legal commentary argues tampering voids a
  warranty *only if it directly caused the defect*, and that sellers "cannot deny warranty by
  shifting blame unless misuse is proven" — but that is **secondary commentary, not confirmed
  statute**.
- **Rooting/modding is not illegal in India.** The risk is to *warranty coverage*, not legality.
- **Enforcement is at Ola's discretion.** It is a real *practical* risk, especially if a fault
  is linked to the mod; sources disagree on whether a blanket denial could be contested.
- For comparison, the EU's FSFE position is that *merely* modifying device software by
  rooting/flashing is not by itself a sufficient reason to void a statutory warranty. That is
  EU law, not India.

## 4. Why the risk here is comparatively low — and how to minimise it

S1Mods is deliberately built to shrink this exposure (see [`SAFETY.md`](SAFETY.md)):

- It **only touches the Android infotainment head unit** — never the **battery, BMS, motor, or
  throttle** — so it has no technical path to cause the defects the big battery warranty covers.
- It makes **one persistent change** (`scootermode`) and is **fully reversible**.

**Before any service visit or OTA:**

1. **S1Mods → Health → Restore stock state** (or `python setup.py --revert`), then **reboot** —
   restores the captured stock `scootermode` and re‑locks ADB.
2. **S1Mods → Health → Remove** each mod (or `python setup.py --uninstall`) — reverts grants and
   removes the apps.
3. Keep **MoveOS updated**, since letting it go stale is itself a listed exclusion.

After that there is nothing modded for a service centre to see, and the vehicle is back to its
captured stock state.

## Sources

- [Ola Electric — Battery Warranty Terms & Conditions](https://www.olaelectric.com/battery-warranty-tnc)
- [Ola Electric — Battery Warranty](https://www.olaelectric.com/battery-warranty)
- [Ola Electric — FAQ](https://www.olaelectric.com/faq)
- [meraev — EV Scooter Battery Warranty in India (2026)](https://www.meraev.com/blog/electric-scooter-battery-warranty-in-india-explained-2026-whats-covered-what-voids-it-and-how-to-claim)
- [ev.care — Ola S1 Warranty Guide](https://ev.care/blog/ola-s1-warranty-guide)
- [FSFE — Does rooting/flashing void your statutory warranty? (EU)](https://fsfe.org/activities/android/flashingdevices.en.html)
- [worldlawdigest — Is Rooting Legal in India?](https://www.worldlawdigest.com/india/is-rooting-legal-in-india)
- [law4u — Does Altering A Product Void Its Warranty? (India)](https://www.law4u.in/top-answer/2348/does-altering-a-product-void-its-warranty)
