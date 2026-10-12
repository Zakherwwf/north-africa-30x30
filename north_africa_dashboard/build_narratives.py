"""Narrative report text for the dashboard, written from data/countries.json and the regional totals.

Each row: scope (REGION or ISO3), order, section, heading, text. Numbers in the text come from the datasets.
"""
import json, os

WS = os.environ.get("VARIANT") == "ws"   # second site: Morocco including Western Sahara
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wwf_site_ws" if WS else "", "data")
c = {r["iso3"]: r for r in json.load(open(f"{D}/countries.json"))}
k = json.load(open(f"{D}/kbas.json"))
f0 = lambda x: f"{x:,.0f}"
f1 = lambda x: f"{x:,.1f}"
f2 = lambda x: f"{x:,.2f}"

L = sum(r["land_km2"] for r in c.values()); S = sum(r["sea_km2"] for r in c.values())
CL = sum(r["covered_land_km2"] for r in c.values()); PL = sum(r["pa_land_km2"] for r in c.values()); OL = sum(r["oecm_land_km2"] for r in c.values())
CS = sum(r["covered_sea_km2"] for r in c.values())
mt = [x for x in k if x["mountain"] == "Y"]; mr = [x for x in k if x["marine"] == "Y"]
avg = lambda rows: sum(x["covered_pct"] for x in rows) / len(rows)

rows = []
def add(scope, section, heading, text):
    rows.append(dict(scope=scope, order=len([r for r in rows if r["scope"] == scope]) + 1, section=section, heading=heading, text=text))

R = "REGION"
add(R, "summary", "The region at a glance",
    f"Across Tunisia, Algeria, Morocco, Libya and Egypt, protected areas and OECMs cover {f0(CL)} km², or {f1(CL / L * 100)}% of the region's "
    f"{f0(L)} km² of land, and {f0(CS)} km², or {f1(CS / S * 100)}%, of its {f0(S)} km² of sea. " + (f"Only Algeria passes 30% on land ({f1(c['DZA']['land_pct'])}%); Morocco, with Western Sahara included, reaches {f1(c['MAR']['land_pct'])}%. None comes close at sea."
    if WS else f"Two countries pass 30% on land, Algeria ({f1(c['DZA']['land_pct'])}%) and Morocco ({f1(c['MAR']['land_pct'])}%); none comes close at sea."))
add(R, "oecm", "OECMs carry the land figure",
    f"Protected areas alone cover {f1(PL / L * 100)}% of the region's land. OECMs add {f1(OL / L * 100)} points, all of it from two countries: "
    f"Algeria's five Saharan Cultural Parks ({f0(c['DZA']['oecm_land_km2'])} km²) and Morocco's permanent hunting reserves and SIBEs "
    f"({f0(c['MAR']['oecm_land_km2'])} km²). Tunisia, Libya and Egypt report no OECMs. Whether these areas meet the CBD criteria for OECMs "
    "(decision 14/8) is a national judgement that each report should document; their effectiveness evidence is thin.")
add(R, "sea", "The sea is the regional gap",
    f"Marine coverage ranges from {f2(c['DZA']['sea_pct'])}% in Algeria to {f2(c['EGY']['sea_pct'])}% in Egypt. Reaching 30% across the region's "
    f"waters would take another {f0(0.3 * S - CS)} km². No country has an OECM at sea of any size, and several marine protected areas "
    "(Morocco's Mogador, Alboran, Massa and Agadir) are still only proposed.")
add(R, "kba", "Key Biodiversity Areas",
    f"The region's {len(k)} KBAs are on average {f1(avg(k))}% covered, and {sum(1 for x in k if x['coverage_class'] == 'None')} have no coverage at all. "
    f"Mountain KBAs ({len(mt)}) are the least covered group, at {f1(avg(mt))}% on average, with {sum(1 for x in mt if x['covered_pct'] == 0)} uncovered, "
    f"most of them in the Tell and Aurès ranges of northern Algeria. Marine KBAs ({len(mr)}) average {f1(avg(mr))}%.")
add(R, "ecosystems", "Representation",
    "Coverage follows the desert. Within Algeria, most Saharan ecoregions are 45–100% covered through the Cultural Parks, while across the region the "
    "Mediterranean woodlands and forests are about 12% covered and the Nile Delta under 1%. Freshwater habitats are poorly covered "
    "everywhere except the salt flats: marshes and river floodplains rarely exceed 20%.")
add(R, "governance", "Governance and effectiveness",
    "Almost all reported area is governed by national governments; the exception is Morocco, where 88% of covered land is reported as collaborative "
    f"governance. Egypt has no governance type for {f1(c['EGY']['gov_not_reported_pct'])}% of its covered land. Effectiveness evidence is weak across "
    "the board: no evaluation in the region carries a score, and only a handful are less than five years old.")
add(R, "data", "Data gaps that change the numbers",
    "Libya's WDPA holds five point sites while its strategy lists more than 40 declared reserves and wetlands; Egypt has 13 large protected areas "
    "proposed since 1999; Morocco has 42 proposed sites, including its new natural parks. Updating the WDPA would move every figure in this dashboard "
    "more than any methodological choice.")
add(R, "method", "How the numbers were made",
    "Each country was processed with the same pipeline: WDPA and WD-OECM October 2026; proposed sites and UNESCO biosphere reserves removed; points "
    "buffered to circles of their reported area; land and sea measured in Mollweide equal-area projection; protected areas dissolved; OECMs measured "
    "after erasing protected areas. KBAs use the official polygons (September 2026); ecosystems use RESOLVE ecoregions and Marine Ecoregions of the "
    "World; inland waters use HydroRIVERS and GLWD v2. Each country's workbook was recalculated in Excel with zero formula errors.")

MAR_WS = [
  ("summary", "Summary", f"With Western Sahara included, Morocco covers {f2(c['MAR']['land_pct'])}% of its land: {f2(c['MAR']['land_pa_pct'])}% in protected "
   f"areas and {f2(c['MAR']['land_oecm_pct'])}% in 338 OECMs, {f0(c['MAR']['land_needed_km2'])} km² short of 30%. The sea is at {f2(c['MAR']['sea_pct'])}%, "
   f"{f0(c['MAR']['sea_needed_km2'])} km² short of 30%. Western Sahara adds 269,939 km² of land and 285,374 km² of sea but no WDPA or WD-OECM site; "
   "without it, the figures are 33.70% and 0.33%, as on Protected Planet."),
  ("oecm", "The OECM question", "221 permanent hunting reserves, all reported in 2021 under collaborative governance, supply 18.0 points of the land "
   "figure. None has an effectiveness evaluation. Their biodiversity outcomes need documenting before they carry a national 30x30 claim."),
  ("ecosystems", "Ecosystems and inland waters", f"Mediterranean woodlands and forests are 14.9% covered and the argan woodlands 20.3%. The desert "
   f"ecoregions of Western Sahara, the Saharan Atlantic coastal desert and the South Sahara desert, have no coverage. Lakes and wetlands are "
   f"{f1(c['MAR']['wetlands_pct'])}% covered; the Saharan Upwelling marine ecoregion 0.07%."),
  ("kba", "Key Biodiversity Areas", f"The 73 KBAs average {f1(c['MAR']['kba_mean_pct'])}%, but only {f1(c['MAR']['kba_mean_pa_pct'])}% from protected areas. "
   "The six KBAs of Western Sahara have no coverage; the largest uncovered KBA areas are the Dakhla area and the Canary Current shelf sites offshore."),
  ("governance", "Governance and effectiveness", "88% of covered land is under shared governance. No evaluation is less than five years old."),
  ("next", "What would move the figure", "Designating the 42 proposed sites in the WDPA, among them the new natural parks and five marine protected areas, "
   "and reporting any protected areas in Western Sahara, would raise the protected-area figure and start to close the marine gap."),
 ]

N = {
 "TUN": [
  ("summary", "Summary", f"Protected areas cover {f2(c['TUN']['land_pct'])}% of Tunisia's land and {f2(c['TUN']['sea_pct'])}% of its sea, close to the "
   f"7th National Report's 7.86% and 1.1%. Reaching 30% would take {f0(c['TUN']['land_needed_km2'])} km² more on land and {f0(c['TUN']['sea_needed_km2'])} km² at sea. "
   "Most wetlands are listed twice, as a national wetland zone and as a Ramsar site, so flattening removes more than a third of the summed area."),
  ("ecosystems", "Ecosystems and inland waters", f"Coverage leans on the salt flats: Chott Jrid alone is 40% of protected land. Lakes and wetlands are "
   f"{f1(c['TUN']['wetlands_pct'])}% covered, mostly salt pans, while the Mediterranean woodlands and forests of the north are 2.3% covered."),
  ("kba", "Key Biodiversity Areas", f"The 72 KBAs average {f1(c['TUN']['kba_mean_pct'])}%; only {c['TUN']['kba_complete']} are fully covered and "
   f"{c['TUN']['kba_none']} have none, including the Gafsa steppe and Jbel Zaghouan."),
  ("governance", "Governance and effectiveness", "Nearly all covered land is government-governed. Only Ichkeul has an evaluation from the last five years "
   "(World Heritage Outlook 2025), and none has a score."),
  ("next", "What would move the figure", "Designating the north's forests and Mediterranean coast, and adding marine protected areas around the Zembra, "
   "Kerkennah and Kuriat islands, would address the weakest parts of the network."),
 ],
 "DZA": [
  ("summary", "Summary", f"Algeria covers {f2(c['DZA']['land_pct'])}% of its land: {f2(c['DZA']['land_pa_pct'])}% in protected areas and "
   f"{f2(c['DZA']['land_oecm_pct'])}% in five Saharan Cultural Parks reported as OECMs. The sea is at {f2(c['DZA']['sea_pct'])}%, "
   f"{f0(c['DZA']['sea_needed_km2'])} km² short of 30% and about 6,500 km² short of the national 5% target."),
  ("oecm", "The OECM question", "The Cultural Parks protect cultural and natural heritage together. Their OECM status rests on Algeria's own "
   "reporting; each has one METT assessment from 2011. A report should give the protected-area and OECM figures separately."),
  ("ecosystems", "Ecosystems and inland waters", "The Saharan ecoregions are well covered through the Cultural Parks; the Mediterranean woodlands and "
   "conifer forests of the Tell are 13% and 9% covered, with no OECM contribution. Salt pans are 85% covered, marshes 15%."),
  ("kba", "Key Biodiversity Areas", f"The 65 KBAs average {f1(c['DZA']['kba_mean_pct'])}% ({f1(c['DZA']['kba_mean_pa_pct'])}% by protected areas alone). "
   f"Mountain KBAs average {f1(c['DZA']['kba_mountain_pct'])}%, and the largest uncovered areas are Aurès–Chélia, the Dahra and Monts des Traras."),
  ("governance", "Governance and effectiveness", f"The Tassili n'Ajjer World Heritage site and Djebel Aïssa National Park have no governance type, leaving {f1(c['DZA']['gov_not_reported_pct'])}% "
   "of covered land unreported. Its 2025 World Heritage Outlook is the only current evaluation."),
  ("next", "What would move the figure", "Marine protected areas, and protected areas or OECMs in the northern mountains, would close the gaps that the "
   "land headline hides."),
 ],
 "MAR": MAR_WS if WS else [
  ("summary", "Summary", f"Morocco covers {f2(c['MAR']['land_pct'])}% of its land (Western Sahara excluded): {f2(c['MAR']['land_pa_pct'])}% in protected "
   f"areas and {f2(c['MAR']['land_oecm_pct'])}% in 338 OECMs. The sea is at {f2(c['MAR']['sea_pct'])}%, {f0(c['MAR']['sea_needed_km2'])} km² short of 30%."),
  ("oecm", "The OECM question", "221 permanent hunting reserves, all reported in 2021 under collaborative governance, supply 29.7 points of the land "
   "figure. None has an effectiveness evaluation. Their biodiversity outcomes need documenting before they carry a national 30x30 claim."),
  ("ecosystems", "Ecosystems and inland waters", f"Mediterranean woodlands and forests are 14.9% covered and the argan woodlands 20.8%. Lakes and wetlands are "
   f"{f1(c['MAR']['wetlands_pct'])}% covered; the Saharan Upwelling marine ecoregion 0.1%."),
  ("kba", "Key Biodiversity Areas", f"The 67 KBAs average {f1(c['MAR']['kba_mean_pct'])}%, but only {f1(c['MAR']['kba_mean_pa_pct'])}% from protected areas. "
   "The largest uncovered KBA areas are the two Canary Current shelf sites offshore."),
  ("governance", "Governance and effectiveness", "88% of covered land is under shared governance. No evaluation is less than five years old."),
  ("next", "What would move the figure", "Designating the 42 proposed sites in the WDPA, among them the new natural parks and five marine protected areas, "
   "would raise the protected-area figure and start to close the marine gap."),
 ],
 "LBY": [
  ("summary", "Summary", f"Libya's five WDPA sites, all points, cover {f2(c['LBY']['land_pct'])}% of its land and {f2(c['LBY']['sea_pct'])}% of its sea. "
   f"Reaching 30% would take {f0(c['LBY']['land_needed_km2'])} km² on land and {f0(c['LBY']['sea_needed_km2'])} km² at sea."),
  ("data", "A data gap more than a protection gap", "The NBSAP 2023–2030 describes 11 reserves by 2010 and 30 sites announced in 2021, none of them in "
   "the WDPA. Every figure here rests on circles drawn around five coordinates; El Nagaza alone gives 84% of the land figure and all of the sea figure."),
  ("ecosystems", "Ecosystems and inland waters", "Seven of nine land ecoregions, 96% of the land, have no protection; 0.3% of lakes and wetlands and none "
   "of the salt pans are covered."),
  ("kba", "Key Biodiversity Areas", f"Sixteen of 18 KBAs have no coverage; the average is {f2(c['LBY']['kba_mean_pct'])}%."),
  ("next", "What would move the figure", "Reporting the national network to UNEP-WCMC with boundaries is the single most useful step for Libya's Target 3 reporting."),
 ],
 "EGY": [
  ("summary", "Summary", f"Egypt covers {f2(c['EGY']['land_pct'])}% of its land and {f2(c['EGY']['sea_pct'])}% of its sea with the Halaib Triangle excluded, "
   "and 12.81% and 4.62% with it included. The national target is 20% of protected areas and OECMs by 2030."),
  ("data", "Halaib and proposed sites", "Gebel Elba National Park lies largely in Halaib. Thirteen protected areas proposed in 1999, 56,941 km² including "
   "the Qattara Depression, are excluded until designated; they would bring land coverage to about 17%."),
  ("ecosystems", "Ecosystems and inland waters", "The Red Sea mountains and coast are the best covered; the Nile valley and delta are almost unprotected "
   f"(Nile Delta ecoregion 0.6%, riverine wetlands 0.2%). Lakes and wetlands are {f1(c['EGY']['wetlands_pct'])}% covered."),
  ("kba", "Key Biodiversity Areas", f"The 33 KBAs average {f1(c['EGY']['kba_mean_pct'])}%; {c['EGY']['kba_complete']} are complete and {c['EGY']['kba_none']} "
   "have none, including the Upper Nile and El Qasr desert."),
  ("governance", "Governance and effectiveness", f"{f1(c['EGY']['gov_not_reported_pct'])}% of covered land has no governance type, mainly El-Gelf El-Keber. "
   "Only Wadi Al-Hitan has a current evaluation."),
  ("next", "What would move the figure", "Designating the proposed sites, protecting stretches of the Nile and its wetlands, and filling governance types in "
   "the WDPA."),
 ]}
for iso, secs in N.items():
    for s, h, t in secs:
        add(iso, s, h, t)
json.dump(rows, open(f"{D}/narratives.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(rows), "narrative rows")
