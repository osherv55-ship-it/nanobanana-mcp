# MECHANISM KNOWLEDGE BASE, Part A: peptides, research compounds and GLP-1-class drugs

*Version 2026-10-03. Built for the `bio-protocol-agent` skill. Provenance tags: **[his framing]** = what Bachmeyer says, **[literature]** = the published evidence, **[inferred]** = a reasoned extension that has not been tested directly, **[reg-verified 2026-10-03]** = regulatory status checked on the web today.*

*Quote markers: Bachmeyer quotes were checked against `corpus_raw_norm.txt`. That file is a normalised corpus of transcripts and captions, so the check ignores case, punctuation and transcription spellings such as "macrofages". **[v]** after a quote = found verbatim; **[v, title]** = a verbatim video, chapter or episode title or description. Anything not found verbatim is written without quotation marks and tagged **[paraphrase]**. Quotations attributed to FDA, USADA or published reviews come from those sources, not from the corpus. Hebrew lines are translations.*

---

## 0. How to use this file (read first)

**Hard boundary.** This file contains no doses, amounts, routes, frequencies, cycle lengths, timing, reconstitution steps or sourcing for any compound in it. That includes approved drugs and his own numbers, even when attributed to him. If a user asks "how much / how often / how do I inject", the agent answers: *"That is a decision for a physician who can examine you, read your labs and prescribe a regulated product. Here is what the compound does, what the evidence shows and what to ask your doctor."* Every if/then in this file ends in a safe action: **stop, retest, or see the physician.** For a drug that a physician has prescribed, the safe action is always **contact the prescriber**. The user never stops or changes a prescribed drug on their own.

**The Big Three (his framework) [his framing]:** (1) **systemic inflammation**, "the fire"; (2) **insulin resistance**, "the fuel problem"; (3) **ATP shortage / mitochondrial dysfunction**, "the power outage" [v]. As a teaching heuristic these are real, measurable and interconnected axes [literature]. What the evidence does *not* support is the step from "touches one axis in a rat" to "treats disease in a human" [literature].

**Evidence grades:** A = human RCTs or meta-analysis for this indication · B = small RCTs or surrogate endpoints · C = observational, or small inconsistent trials · D = animal or in-vitro only. Many compounds carry **split grades by indication**. Never collapse them into one letter.

**The central finding [literature]:** for the signature peptides, mechanistic richness and clinical evidence point in opposite directions. BPC-157, MOTS-c, Epitalon and TB-500 each have specific, interesting molecular mechanisms. Each also has between zero and three small, uncontrolled human studies. Mechanism is not evidence. Four cases where the mechanism was right and the outcome trial still failed:
- elamipretide in primary mitochondrial myopathy (n=218, negative);
- thymosin α1 in sepsis (n=1,106, HR 0.99);
- low-dose naltrexone in fibromyalgia (Part B);
- semaglutide in early Alzheimer's (EVOKE/EVOKE+, n=3,808, no slowing on CDR-SB).

### 0.1 Regulatory snapshot (as of 2026-10-03)

**FDA, 503A/503B compounding [reg-verified 2026-10-03]:**
- **15 Apr 2026:** FDA removed 12 peptides from 503A Category 2 because the nominations were withdrawn: BPC-157, LL-37, Dihexa, Emideltide (DSIP), Epitalon, GHK-Cu (injectable), KPV, PEG-MGF, Melanotan II, MOTS-c, Semax and TB-500 (LKKTETQ). Removal is **not** approval and **does not** make a substance eligible for compounding.
- The FDA page dated 22 Apr 2026 also lists thymosin α1, CJC-1295, AOD-9604 and Selank in the "nominated but withdrawn" table. That page keeps FDA's safety language: immunogenicity, impurity/API characterisation, and "lacks sufficient information to know whether the drug would cause harm".
- **Still ACTIVE Category 2** on that page: **Kisspeptin-10** (503A, added 29 Sep 2023); **Ipamorelin**, **ibutamoren (MK-677)**, GHRP-2, GHRP-6 (503B).
- **23–24 Jul 2026, PCAC:** the advisory committee recommended adding BPC-157 (8–6, 1 abstention), KPV, TB-500, MOTS-c (7–5, 2 abstentions), Epitalon and Semax to the 503A Bulks List. It voted **against** Emideltide/DSIP (7–6, 1 abstention). The votes are non-binding and need FDA rulemaking. They establish **no** safety, efficacy, dose or indication.
- Not on the Category pages: SS-31, NAD+, retatrutide, 5-Amino-1MQ [per corpus check].

**WADA 2026 Prohibited List** [corpus, from the 2026 PDF]:

| Section | Compounds |
|---|---|
| S0 (non-approved substances, named) | BPC-157 |
| S2.3 (growth factors and modulators) | Thymosin-β4 and derivatives incl. TB-500; mechano growth factors (MGFs); IGF-1 and its analogues |
| S2.2.1 (testosterone-stimulating peptides in males — prohibited in males) | Kisspeptin and its agonist analogues |
| S2.2.3 | AOD-9604 (named GH fragment); growth hormone |
| S2.2.4 | CJC-1295, sermorelin, tesamorelin, ipamorelin, ibutamoren |
| S4.4.1 (metabolic modulators, prohibited at all times) | MOTS-c (AMPK activator); GW1516/Cardarine (PPARδ agonist); SR9009, SR9011 (Rev-erb agonists) |
| S1.2 | SARMs |
| S1.1 | Testosterone |
| Monitoring Program (**not** prohibited) | Nicotine |

Not named: Epitalon, GHK-Cu, thymosin α1, NAD+, methylene blue, approved GLP-1s. Unapproved compounds (for example retatrutide) fall under the S0 catch-all [inferred from S0 wording].

**Israel (Ministry of Health): REGISTRY UNAVAILABLE. Treat every Israel line in this file as unconfirmed unless it is marked as web-verified.**
- The MoH drug registry was unavailable during research, so no research peptide's status could be verified. None is known to be registered [inferred]. Verify at israeldrugs.health.gov.il before stating otherwise.
- Verified by web: Wegovy is registered and marketed (since Apr 2024). In Apr 2024 the MoH barred sale of Ozempic for weight loss. Mounjaro has been marketed since Sep 2024. News reports say the 2026 health basket added Wegovy for adolescents aged 12–18 [news reports only; verify with the health funds].

---

## 1. Tissue-repair and immune peptides

### 1.1 **BPC-157** (Body Protection Compound-157)

- **Class:** synthetic 15-amino-acid partial sequence of a gastric-juice protein. Unapproved research compound. [literature]
- **Big Three assignment:** primarily **systemic inflammation** ("the systemic firefighter" [v]) plus tissue repair. Secondarily ATP ("BPC requires energy" [v]) and insulin resistance, which appears in his disease list. [his framing]
- **His framing:**
 - "It's just a signal. It's a very specific signal." [v]
 - "If I could only pick one peptide what would I do? BPC. I wouldn't even think twice." [v]
 - "Master regulator of the VEGF system." [v]
 - He says there is "no evidence of BPC 157 toxicity, organ damage or cancer promotion whatsoever" [v]. He also claims it is anti-cancer, enhances p53 and CD8+ infiltration, and repairs the kidney, heart, brain and gut [paraphrase].
- **Real mechanism (chain) [literature]:**
 1. **No identified receptor.** It is a key that opens doors, but nobody has found the lock.
 2. **Upregulates VEGFR2** on endothelial cells. This is the permit office that approves new pipe. That drives **Akt → eNOS → nitric oxide**, the valve that opens the line, which leads to **angiogenesis** (new blood-vessel plumbing to the job site).
 3. **FAK–paxillin phosphorylation** in fibroblasts. The crew grabs the scaffolding and crawls to the damaged wall: more fibroblast migration and spreading.
 4. **ERK1/2 activation**, the foreman's radio relaying "build" orders.
 5. **Cytoprotection under oxidative stress** in rodent gut mucosa (a fire-retardant coat on the stomach lining), plus modulation of NO and dopamine/serotonin systems in rodent CNS models.
 6. Essentially **all of this is rat or in-vitro**.
- **Body systems affected:** GI mucosa; tendon, ligament and muscle; vascular endothelium; CNS (rodent only).
- **Human evidence [literature]:** three pilot efforts in total:
 - a retrospective knee chart review (16 contacted patients, no control, no validated outcome instruments);
 - an interstitial cystitis report;
 - a phase 1 safety/PK study whose results were never posted.
 - Two 2026 reviews: 67% of the peptide literature is preclinical; human benefits "remain unsubstantiated".
- **Evidence grade: D.**
- **Key risks:**
 - **Angiogenesis cuts both ways.** The VEGFR2 mechanism is also the basis of a theoretical tumour-promotion concern [literature]. Do not use with active or suspected cancer, or a recent cancer history, without an oncologist [inferred].
 - USADA: unknown whether **any** safe dose exists. FDA: immunogenicity, peptide impurities, API characterisation.
 - Grey-market identity and purity are unverified.
 - No human interaction data. Pregnancy and breastfeeding: no data, avoid [inferred].
 - *Contradiction to flag:* he insists that one delivery form of BPC-157 can never work [paraphrase]. Yet several of Sikiric's foundational rat studies, the evidence he cites, used that same form [literature]. His own sources contradict his rule.
- **What he stacks it with (names only):** TB-500, GHK-Cu (the "Wolverine" stack [v]); MOTS-c; NAD+; KPV; Thymosin α1 + Epitalon + MOTS-c (the "four peptides for life" [v, title]); Retatrutide (liver); Cerebrolysin + KPV (tinnitus); Selank + Aniracetam (anxiety); ARA-290 (NAFLD).
- **Regulatory:**
 - FDA: not approved. Removed from Category 2 in Apr 2026 (nomination withdrawn). PCAC recommended Bulks-List inclusion 8–6 in Jul 2026; this is non-binding. [reg-verified 2026-10-03]
 - WADA: **S0, named**.
 - Prescription-controlled in Australia and New Zealand.
 - Israel: not registered/not verified.
- **Gap between claim and evidence:** "The one peptide" for everything from kidneys to cancer rests on rat and cell data, plus 16 uncontrolled knees.
 - בעברית: "הפפטיד האחד" לכל דבר נשען על חולדות ותאים. אין אף ניסוי מבוקר בבני אדם.

### 1.2 **TB-500 / Thymosin β4 (Tβ4)**

- **Class:** Tβ4 is a 43-amino-acid endogenous actin-sequestering peptide. **TB-500 is a different molecule**: the short LKKTETQ fragment. He calls the difference "incremental" [v]. [literature / his framing]
- **Big Three assignment:** inflammation and tissue repair; he adds cardiac restoration. [his framing]
- **His framing:**
 - "It binds to actin." [v]
 - "TB 500 is like the foreman." [v]
 - "It's the only thing on the planet that'll heal the myocardium." [v]
 - He concedes it may accelerate existing tumour growth [paraphrase, via a third-party summary].
- **Real mechanism (chain) [literature]:**
 1. **Binds monomeric G-actin 1:1.** It holds the bricks on the pallet until the crew needs them, buffering the **F-/G-actin equilibrium**.
 2. This lets the cytoskeleton remodel, so cells **migrate**: workers can walk to the wound.
 3. **Stem/progenitor mobilisation, anti-apoptotic and anti-inflammatory effects, angiogenesis.** The crew calls in subcontractors and lays new pipe.
 4. Enzymes (meprin-α, prolyl oligopeptidase) cleave it to **Ac-SDKP**, an antifibrotic tetrapeptide: the clean-up crew that stops scar concrete from setting.
 5. A putative receptor (Ku80) is proposed but not cloned.
- **Body systems affected:** skin and cornea (human); heart, liver, muscle and tendon (animal only).
- **Human evidence [literature]:**
 - **Full-length Tβ4, topical/ophthalmic only:** phase 2 trials in pressure ulcers, venous ulcers and epidermolysis bullosa; phase 3 in dry eye / neurotrophic keratopathy.
 - **TB-500 fragment:** per FDA, *no identified human exposure data*.
 - No human cardiac, orthopaedic or athletic data for either.
- **Evidence grade:** **B-/C** for topical Tβ4 (eye, chronic wounds); **D** for systemic TB-500.
- **Key risks:**
 - Pro-migration and pro-angiogenic biology is double-edged. High Tβ4 expression is associated with invasiveness in several tumour types [literature].
 - FDA: immunogenicity and aggregation.
 - Fragment and full-length molecule are routinely confused in marketing.
 - Central to the Essendon/Cronulla doping scandals.
- **What he stacks it with:** BPC-157, GHK-Cu (Wolverine); MOTS-c (heart failure); KPV, Retatrutide (liver lists).
- **Regulatory:**
 - FDA: not approved. Removed from Category 2 in Apr 2026. Among the PCAC-recommended six in Jul 2026 (non-binding).
 - WADA: **S2.3, named**.
 - Israel: not verified.
- **Gap:** "Heals the myocardium" comes from mouse hearts. The only human data are for eye drops and wound gels of a different, full-length molecule.
 - בעברית: "מרפא את שריר הלב" — עכברים. בבני אדם יש נתונים רק לטיפות עיניים של מולקולה אחרת.

### 1.3 **Thymosin α1** (thymalfasin, Zadaxin)

- **Class:** 28-amino-acid synthetic thymic peptide, an immunomodulator. Approved in about 35 countries, **not the US**. [literature]
- **Big Three assignment:** **systemic inflammation** ("failure number one" [v], immune recalibration). He also calls insulin resistance "a very big immune problem" [v]. [his framing]
- **His framing:**
 - "It doesn't boost or suppress, to be honest. It trains." [v]
 - The thymus is "the boot camp for T cells" [v].
 - Claims it is "FDA approved as an adjunctive therapy" [v] for melanoma and hepatitis B [paraphrase]. **False for the US.**
- **Real mechanism (chain) [literature]:**
 1. **Agonist at TLR2 and TLR9** on dendritic and myeloid cells. It rings the alarm bell at the guardhouse.
 2. **HLA-DR ↑ / antigen presentation:** the guards hold up the wanted poster.
 3. **T-cell maturation and Th1 cytokines (IFN-γ, IL-2):** the drill sergeant turns recruits into soldiers.
 4. **NK-cell cytotoxicity ↑:** the special-forces unit gets live ammo.
 5. Mechanistically this is an **immune stimulant**, not a neutral "trainer" [inferred from the TLR-agonist mechanism].
- **Body systems affected:** innate and adaptive immunity, liver (hepatitis indication).
- **Human evidence [literature]:**
 - Chronic hepatitis B: 7 RCTs showed higher sustained virologic response.
 - **Sepsis:** about a dozen small positive trials, then the definitive **TESTS phase 3 (n=1,106) was null** (HR 0.99).
 - COVID reviews conflict. Oncology-adjuvant use is still under study.
- **Evidence grade:** **B** for chronic hepatitis B where licensed; **negative** for sepsis; **D** for "immune optimisation" or longevity.
- **Key risks (double-edged immune stimulation):**
 - Theoretical flare risk in autoimmune disease [inferred].
 - Rejection risk in transplant recipients; antagonises immunosuppressants [inferred]. Physician-only in these groups.
 - Injection-site irritation. Generally well tolerated in the licensed indication.
 - FDA flags immunogenicity for compounded product.
- **What he stacks it with:** BPC-157, MOTS-c, Epitalon (the "four peptides for life" [v, title]); LL-37 (the "Kangaroo Protocol" [v, title], for plaque); nicotine + BPC-157 (arrhythmia anecdote: "I've seen them eradicated" [v]).
- **Regulatory:**
 - FDA: not approved; withdrawn-nomination table (FDA page 22 Apr 2026).
 - WADA: not named (approved abroad, so S0 likely does not apply [inferred]).
 - Israel: not verified.
- **Gap:** Calling it a gentle "trainer" hides that it is a TLR-agonist immune stimulant, and its largest trial (sepsis) failed.
 - בעברית: הוא לא "מאמן ניטרלי" אלא ממריץ חיסוני, והניסוי הגדול ביותר שלו נכשל.

### 1.4 **GHK-Cu** (copper tripeptide)

- **Class:** endogenous plasma tripeptide (Gly-His-Lys) chelating Cu(II). Cosmetic ingredient (topical); unapproved injectable. [literature]
- **Big Three assignment:** **all three**. He says copper delivery to Complex IV fixes ATP, and that it hits inflammation and insulin resistance. [his framing]
- **His framing:**
 - "Three amino acids, one copper ion." [v]
 - "It's not a skin peptide." [v]
 - "GHK-Cu is the finisher." [v]
 - Paired with BPC-157 it gives "neuronal armor that is almost impenetrable." [v]
 - Says it resets gene expression in "over 4,000 genes" [v].
- **Real mechanism (chain) [literature]:**
 1. Plasma level falls with age (about 200 ng/mL at 20 to 80 ng/mL at 60). It binds **Cu(II)** with high affinity: the delivery truck carrying copper wiring.
 2. At pico- to nanomolar levels it stimulates **fibroblast collagen, elastin, decorin and GAG synthesis**, restocking the rebar and mesh.
 3. **MMP/TIMP balance:** the demolition crew versus the brakes on demolition.
 4. **Chemoattraction of immune and endothelial cells** to the injury, calling the trades to the site.
 5. *His Complex IV claim:* copper really is a cofactor of cytochrome c oxidase [literature]. But there is no human evidence that GHK-Cu raises Complex IV activity or ATP [inferred].
 6. The "4,000 genes" figure comes from gene-expression work by Loren Pickart, who commercialises the peptide. Treat it as a conflicted primary source.
- **Body systems affected:** skin and hair (human, topical); wound healing (animal); vasculature.
- **Human evidence [literature]:** several small, short topical facial studies (firming, photodamage). A 2024/25 review notes "a surprising absence of clinical studies". No injectable musculoskeletal data.
- **Evidence grade:** **C** topical cosmetic; **D** injectable/systemic.
- **Key risks:**
 - Copper load: contraindicated in Wilson disease and copper-overload states [inferred]. Zinc–copper balance matters.
 - Angiogenic signalling (theoretical tumour concern) [inferred].
 - FDA flags injectable GHK-Cu for immunogenicity/aggregation with "limited data in humans".
 - Contact allergy (topical).
- **What he stacks it with:** BPC-157, TB-500 (Wolverine/GLOW blends); NAD+; MOTS-c, Epitalon (anti-aging); zinc (copper balance).
- **Regulatory:**
 - FDA: injectable removed from Category 2 in Apr 2026; not among the PCAC-reviewed seven; topical sold as a cosmetic.
 - WADA: not named.
 - Israel: topical cosmetics probably available [inferred]; injectable not verified.
- **Gap:** "Not a skin peptide" — skin is the only place it has any human data.
 - בעברית: "זה לא פפטיד לעור" — אבל העור הוא המקום היחיד עם נתונים בבני אדם.

### 1.5 **KPV** (Lys-Pro-Val)

- **Class:** C-terminal tripeptide of α-MSH. Research compound. [literature]
- **Big Three assignment:** **systemic inflammation** (he says it resolves rather than suppresses inflammation [paraphrase]). [his framing]
- **His framing:**
 - Video title: "Inflammation is killing you, KPV is the answer." [v, title]
 - "Binds to receptors on macrophages, basically tells them to chill out." [v]
 - Claims it "makes statins obsolete" [v] and replaces prednisone [paraphrase].
- **Real mechanism (chain) [literature]:**
 1. It is the tail end of α-MSH, the body's own "calm-down" hormone.
 2. It is taken up into colonic epithelial and immune cells via the **PepT1 transporter**, a side door into the cell.
 3. Inside, it inhibits **NF-κB and MAPK** inflammatory signalling, cutting power to the alarm siren.
 4. In mouse colitis this lowers IL-6, TNF-α and IL-1β.
 5. Whether it acts through melanocortin receptors is unresolved.
- **Body systems affected:** gut mucosa (mouse), skin (in-vitro).
- **Human evidence:** none. Mouse colitis models and nanoparticle-delivery studies only.
- **Evidence grade: D.**
- **Key risks:** human safety essentially unknown. FDA says it "lacks important information regarding any safety issues raised by KPV". Immunomodulation of unknown net effect; grey-market purity.
- **What he stacks it with:** BPC-157; Retatrutide, TB-500, GHK-Cu, Tesamorelin (liver list); Cerebrolysin (tinnitus).
- **Regulatory:**
 - FDA: removed from Category 2 in Apr 2026; PCAC recommended in Jul 2026 (non-binding).
 - WADA: not named (S0 catch-all [inferred]).
 - Israel: not verified.
- **Gap:** "Makes statins obsolete" — no human trial of any kind exists.
 - בעברית: "מייתר סטטינים" — אין אף ניסוי בבני אדם.

### 1.6 Other tissue-repair / immune compounds he names (compact templated entries)

#### **LL-37**
- **Class:** human cathelicidin antimicrobial peptide (active fragment of hCAP18). Research compound. [literature]
- **Big Three (his framing):** he does not assign it to an axis; he uses it to clear arterial plaque [his framing]. Closest axis: inflammation [inferred].
- **Verified quote:** chapter "Clearing arterial plaque with LL 37" [v, title].
- **Real mechanism [literature]:** membrane-disrupting antimicrobial; immune chemoattractant (the bouncer that also calls the cops). Complexes with self-DNA/RNA can activate plasmacytoid dendritic cells.
- **Human evidence · grade:** small phase 1/2 topical venous-leg-ulcer RCT · **C** (topical wound), **D** systemic. No human plaque data.
- **Key risks:** implicated as an **autoantigen in psoriasis/lupus**; pro-growth in some tumours.
- **Regulatory:** FDA: removed from Cat 2 Apr 2026 (not among the PCAC-reviewed seven) · WADA: not named (S0 catch-all [inferred]) · Israel: not verified.
- **Gap:** "Clearing arterial plaque" has no human data, and mouse work links cathelicidin to plaque formation rather than clearance [literature].

#### **ARA-290** (cibinetide)
- **Class:** 11-amino-acid peptide derived from EPO's helix B; non-erythropoietic. Investigational. [literature]
- **Big Three (his framing):** **ATP** (protects mitochondria via SIRT3/UCP2) and **insulin resistance** (NAFLD, fructose-damaged endothelium) [paraphrase].
- **Verified quote:** "this works synergistically with BPC" [v].
- **Real mechanism [literature]:** agonist at the innate repair receptor (EPOR/CD131 heteroreceptor); tissue-protective and anti-inflammatory signalling without stimulating red-cell production.
- **Human evidence · grade:** small phase 2 RCTs in sarcoidosis and diabetic small-fibre neuropathy · **C**. No NAFLD or mitochondrial outcome data.
- **Key risks:** limited long-term safety; unapproved product identity.
- **Regulatory:** FDA: not approved, not on the Cat 2 page · WADA: fits S2.1.5 "innate repair receptor agonists" [inferred] · Israel: not verified.
- **Gap:** its only human trials are in neuropathy and sarcoidosis; his liver and mitochondrial uses are untested.

#### **PEG-MGF**
- **Class:** pegylated mechano growth factor (IGF-1Ec splice-variant E-peptide). Research compound. [literature]
- **Big Three (his framing):** none; used for muscle repair in an injury stack [paraphrase].
- **Verified quote:** no verbatim quote from him found.
- **Real mechanism [literature]:** E-peptide of the IGF-1Ec splice variant; proposed satellite-cell activation (rodent/in-vitro); pegylation prolongs circulation.
- **Human evidence · grade:** none · **D**. FDA "has not identified any human exposure data".
- **Key risks:** IGF-axis growth signalling; immunogenicity (FDA).
- **Regulatory:** FDA: removed from Cat 2 Apr 2026 · WADA: **S2.3** (mechano growth factors named) · Israel: not verified.
- **Gap:** zero human data of any kind.

#### **Glutathione** (oral supplement vs compounded injectable)
- **Class:** endogenous tripeptide (γ-Glu-Cys-Gly) redox buffer. Oral forms are dietary supplements; non-oral products are compounded. [literature]
- **Big Three (his framing):** **ATP** (mitochondrial antioxidant) and **inflammation** (neuroinflammation in dementia) [paraphrase].
- **Verified quote:** "it's a master antioxidant" [v]; chapter "The truth about oral glutathione supplements" [v, title]. He dismisses oral supplements as a scam [paraphrase].
- **Real mechanism [literature]:** substrate for glutathione peroxidases and glutathione S-transferases; GSH/GSSG redox buffering.
- **Human evidence · grade:** small, mixed human trials · **C/D** for clinical outcomes. One RCT of an oral supplement raised body glutathione stores [literature].
- **Key risks:** bronchospasm reported in people with asthma; compounded-product quality.
- **Regulatory:** oral = dietary supplement; compounded products fall under compounding rules · WADA: not prohibited · Israel: not verified.
- **Gap:** he calls oral forms a scam, yet an oral-supplement RCT did raise body stores; clinical benefit is unproven for every form.

---

## 2. Mitochondrial / "ATP" compounds

### 2.1 **MOTS-c**

- **Class:** 16-amino-acid mitochondrial-derived peptide encoded in the 12S rRNA region of mtDNA. Research compound. [literature]
- **Big Three assignment:** **insulin resistance + ATP shortage**, and he adds inflammation. Combined with retatrutide, he says "they hit all three biological failures" [v]. [his framing]
- **His framing:**
 - "MOTS-c makes you violently insulin sensitive." [v]
 - "A message directly from the engine room to the bridge." [v]
 - "A broken power plant is disease." [v]
 - Claims human menopause and Alzheimer's trials, e.g. a "44% reduction in hot flashes" [v] and "spatial memory improved 44%" [v]. **No such human trials were found.**
- **Real mechanism (chain) [literature]:**
 1. Encoded in the mitochondria's own genome: a memo written in the power plant's own ledger.
 2. It **inhibits the folate cycle and de novo purine synthesis**, so **AICAR accumulates**.
 3. AICAR triggers **AMPK activation**, the low-fuel warning light that makes the plant switch to burning fat. Skeletal muscle is the main target.
 4. Under metabolic stress it **translocates to the nucleus** and regulates **NRF2/antioxidant-response genes**: the plant manager walks into head office and orders fire extinguishers.
 5. It is **exercise-responsive**, hence "exercise mimetic". Also binds CK2 (ROS-CK2A-MYH9 nuclear-transport axis).
- **Body systems affected:** skeletal muscle, liver, adipose tissue (mouse).
- **Human evidence [literature]:**
 - Observational/biomarker only (for example serum MOTS-c as a predictor of ARDS after cardiac bypass).
 - The only clinical programme, CohBar's analog **CB4211**: phase 1a/1b (NCT03998514, n=88, healthy and NAFLD), safety/PK primary. No efficacy indication was advanced.
- **Evidence grade: D** (mechanistically well characterised, clinically unvalidated).
- **Key risks:**
 - No long-term human safety; FDA flags immunogenicity.
 - Additive glucose-lowering with insulin, sulfonylureas or GLP-1 drugs is a theoretical hypoglycaemia risk [inferred]. If on glucose-lowering drugs: physician only.
 - AMPK activation opposes mTOR-driven anabolism, so stacking it with GH secretagogues sends contradictory signals [inferred].
 - The fatigue he describes is unexplained in humans.
- **What he stacks it with:** NAD+; SS-31 (he insists on a specific order of use that has never been tested in humans); Retatrutide; BPC-157; methylene blue (§2.6); 5-Amino-1MQ; Kisspeptin + estradiol + NAD+ (menopause).
- **Regulatory:**
 - FDA: removed from Category 2 in Apr 2026; PCAC recommended 7–5 in Jul 2026 (non-binding).
 - WADA: **S4.4.1, named**.
 - Israel: not verified.
- **Gap:** He claims it reverses insulin resistance and dementia [paraphrase]. The evidence is mouse data plus one phase 1 safety study of an analog. He also insists on a specific dosing order with SS-31 that has never been tested in humans.
 - בעברית: "הופך אותך לרגיש לאינסולין באלימות" — בעכברים. בבני אדם יש רק מחקר בטיחות אחד של אנלוג.

### 2.2 **SS-31 / elamipretide** (Forzinity)

- **Class:** mitochondria-targeted tetrapeptide. **FDA-approved drug** for one rare disease; separately sold as a "research chemical". [literature]
- **Big Three assignment:** **ATP shortage** ("the structural engineer"). [his framing]
- **His framing:**
 - "That's the whole cardiolipin inner mitochondrial membrane repair. That is just money." [v]
 - Chapter title: "SS 31 the structural engineer" [v, title].
 - People "smash the SS 31 like an imbecile" [v] and ignore the order of use he insists on, an order never tested in humans.
 - "Marry this to SS 31 and you are a cancer annihilating machine." [v] (said of a compound he pairs with SS-31)
- **Real mechanism (chain) [literature]:**
 1. Concentrates in the **inner mitochondrial membrane**.
 2. Binds **cardiolipin**, the mortar that holds the turbine housing together.
 3. Stabilises the **cardiolipin–cytochrome c** supercomplex, keeping the conveyor belt on its rails.
 4. Improves **cristae structure and electron-transport coupling**.
 5. Result: **less ROS leak**, fewer sparks thrown off the engine.
 - This is the only compound in this set whose mitochondrial mechanism is regulator-acknowledged (FDA label).
- **Body systems affected:** skeletal and cardiac muscle (Barth syndrome).
- **Human evidence [literature; reg-verified 2026-10-03]:**
 - **Accelerated approval on 19 Sep 2025**, only for muscle strength in **Barth syndrome** (patients ≥30 kg). Pivotal TAZPOWER: 12 patients, crossover; knee-extensor strength as an intermediate endpoint. A confirmatory RCT is required.
 - **MMPOWER-3 (primary mitochondrial myopathy, n=218): NEGATIVE** on both primary endpoints.
 - Heart failure, dry AMD and diabetic-foot programmes remain investigational.
- **Evidence grade:** **A, but narrow** (Barth, accelerated approval); **negative** for primary mitochondrial myopathy; **D** for fatigue, anti-aging or "mito repair".
- **Key risks:** injection-site reactions in nearly all treated patients; eosinophilia; hypersensitivity; renal-function considerations on the label (prescriber's call). Research-grade "SS-31" is not Forzinity: identity and purity are unverified.
- **What he stacks it with:** MOTS-c (in an untested order he insists on), NAD+, Retatrutide.
- **Regulatory:**
 - FDA: approved prescription drug (Barth syndrome only); not on the Category pages.
 - WADA: not named.
 - Israel: not verified.
- **Gap:** The one peptide with a proven mechanism failed its big trial in general mitochondrial disease. "Cancer annihilating" has zero data.
 - בעברית: המנגנון אמיתי — ובכל זאת הניסוי הגדול במחלות מיטוכונדריה נכשל.

### 2.3 **NAD+: injectable vs oral precursors (NMN, NR)**

- **Class:** NAD+ is an endogenous redox cofactor. **Injectable NAD+** is a compounded product. **NMN/NR** are oral dietary-supplement precursors. [literature]
- **Big Three assignment:** **ATP** ("the power supply" [v]). In one episode he claims all three at once. [his framing]
- **His framing:**
 - "The mitochondrial power supply, without it nothing else works." [v]
 - "Oral NAD supplements are a scam." [v]
 - He says injected NAD+ is far better than oral precursors [paraphrase].
 - "The electron shuttle." [v]
- **Real mechanism (chain) [literature]:**
 1. **NAD+ ↔ NADH** carries electrons from fuel breakdown to **Complex I**: the forklift moving electron pallets to the turbine.
 2. It is the obligate substrate for **sirtuins, PARPs and CD38**, the fuel the repair crews burn.
 3. Tissue NAD+ falls with age and in metabolic disease.
 4. **Precursors NR/NMN** enter the **salvage pathway** (NR via NRK1/2; much NMN is converted to NR before uptake) and **reliably raise blood NAD+** (about 2.6-fold in one MCI trial).
 5. CD38/CD73 break down most extracellular NAD+ before it enters cells. Injected NAD+ therefore plausibly works mostly as **precursor delivery**, not as direct mitochondrial loading [inferred].
 6. **Double edge:** in preclinical work, raised NAD+ can **amplify the inflammatory secretions of senescent cells (SASP)** and support tumour metabolism [literature, preclinical].
- **Body systems affected:** all metabolically active tissue; muscle insulin sensitivity (one human RCT).
- **Human evidence [literature]:**
 - **Oral precursors (supplement-tier; evidence-based amounts allowed):**
 - **NMN 250 mg/day for 10 weeks** improved muscle insulin sensitivity (clamp) in 25 prediabetic postmenopausal women (*Science* 2021) — **grade C** for the outcome.
 - **NR 1,000 mg/day for 6 weeks:** no change in insulin sensitivity, mitochondrial function, liver fat or inflammation. **NR 1 g/day in MCI:** no cognitive change.
 - Trials used NMN 250–900 mg/day and NR 250–1,000 mg/day; well tolerated up to about 12 weeks. **No formal Tolerable Upper Intake Level exists for NMN/NR.** Stay within trial ranges and durations.
 - **Injectable NAD+:** only small PK and pilot studies; **no outcome RCT**. Infusion reactions (flushing, nausea, chest tightness, cramping) are reported [literature].
- **Evidence grade:** **B** for raising the NAD+ biomarker (precursors); **C/D** for any clinical outcome; **D** for injectable NAD+ outcomes.
- **Key risks / interactions:**
 - Precursors: no established drug interactions.
 - Theoretical caution with active cancer (tumour NAD+ dependence) [inferred]. Discuss with an oncologist.
 - Injectable: compounded quality, infusion reactions.
- **What he stacks it with:** MOTS-c, BPC-157, methylene blue, SS-31, GHK-Cu, DSIP, 5-Amino-1MQ.
- **Regulatory:**
 - **NMN:** FDA letters of 29 Sep 2025 confirm NMN is lawful as a dietary-supplement ingredient [reg-verified 2026-10-03].
 - Injectable NAD+: not an FDA-approved drug; compounded; not on the Category pages.
 - WADA: not named.
 - Israel: not verified.
- **Gap:** He calls oral forms a scam, yet the only positive human outcome trial used an *oral* precursor, and injectables have no outcome trial at all.
 - בעברית: הוא קורא לפומי "הונאה" — אבל הניסוי החיובי היחיד היה דווקא בתוסף פומי.

### 2.4 **5-Amino-1MQ**

- **Class:** small-molecule **NNMT inhibitor**, not a peptide. Research compound. [literature]
- **Big Three assignment:** **ATP** (NAD+ preservation) and fat loss / insulin resistance. [his framing]
- **His framing:**
 - It "stops the enzyme from depleting your NAD" [v].
 - Elsewhere he calls it "a mitochondrial complex 3 inhibitor" [v] that works "through like a mitochondrial uncoupling" [v]. **That mechanism is wrong.**
 - Cites a human Alzheimer's study (2022, Hershey, *Brain*) [paraphrase; an unverifiable claim he makes]. **No such human trial is known.**
- **Real mechanism (chain) [literature]:**
 1. Blocks **NNMT (nicotinamide N-methyltransferase)**. NNMT is the leak in the NAD tank: it stamps a methyl tag on nicotinamide and throws it out.
 2. More nicotinamide is **recycled to NAD+**, and **SAM (the methyl-donor currency)** is spared in fat cells.
 3. In diet-induced-obese mice: **smaller adipocytes, less white fat, lower body weight and cholesterol**. Some aged-mouse muscle-regeneration data.
- **Body systems affected:** adipose tissue, muscle (mouse).
- **Human evidence:** none.
- **Evidence grade: D.**
- **Key risks:** no human PK or safety. NNMT sits in methylation balance (SAM/SAH, homocysteine): unknown effects [inferred]. Product identity unverified.
- **What he stacks it with:** Retatrutide + Tesamorelin (the "nuclear option" [v, title]); MOTS-c; NAD+.
- **Regulatory:** FDA not approved; not on the Category page (corpus check). WADA not named (S0 catch-all [inferred]). Israel not verified.
- **Gap:** He gets the mechanism wrong and cites human dementia data that do not exist. Only mouse fat-loss data are real.
 - בעברית: המנגנון שהוא מתאר שגוי, והמחקר בבני אדם שהוא מצטט לא קיים.

### 2.5 Other "mitochondrial / exercise-mimetic" research compounds (compact templated entries)

#### **SLU-PP-332**
- **Class:** synthetic small molecule, pan-ERR (estrogen-related receptor) agonist. Research compound. [literature]
- **Big Three (his framing):** **ATP** (mitochondrial biogenesis) and fat loss / **insulin resistance**; framed as an exercise mimetic and the holy grail of a fat-loss protocol [paraphrase].
- **Verified quote:** episode titles "SLU PP 332 the owners manual" and "The real power of SLU PP 332" [v, title]. His exercise-mimetic framing was not found verbatim for this compound.
- **Real mechanism [literature]:** ERRα/β/γ agonist → mitochondrial-biogenesis and oxidative-fibre gene programmes (mouse).
- **Human evidence · grade:** mouse only · **D**.
- **Key risks:** unknown human toxicity; grey-market formulation hazards.
- **Regulatory:** FDA: not approved · WADA: not named (S0 [inferred]) · Israel: not verified.
- **Gap:** sold as a replacement for exercise with no human data at all.

#### **SR9009** (Stenabolic)
- **Class:** synthetic REV-ERBα/β agonist. Research compound; listed by his company [corpus].
- **Big Three (his framing):** none stated by him; the product listing frames it as metabolic/endurance [corpus]. Closest axes: insulin resistance / ATP [inferred].
- **Verified quote:** no verbatim quote from him found.
- **Real mechanism [literature]:** REV-ERBα/β agonist (circadian clock repressor); poor bioavailability; some effects are REV-ERB-independent.
- **Human evidence · grade:** mouse only · **D**.
- **Key risks:** unknown human safety.
- **Regulatory:** FDA: not approved · WADA: **S4.4.1 (Rev-erb agonists), prohibited at all times** · Israel: not verified.
- **Gap:** a product listing with no human data, and a named banned substance for athletes.

#### **Cardarine** (GW-501516)
- **Class:** PPARδ agonist; abandoned drug candidate. [literature]
- **Big Three (his framing):** **insulin resistance** (fat oxidation, NAFLD, T2D) and **inflammation** (lower NF-κB/ROS, lipotoxicity) [paraphrase].
- **Verified quote:** "cardio in a bottle" [v]; video "Cardarine and the cancer lie" [v, title].
- **Real mechanism [literature]:** PPARδ agonist → muscle fat oxidation, fibre-type shift.
- **Human evidence · grade:** early-phase human lipid studies · **C** (lipids) / **D** outcomes.
- **Key risks:** **GSK abandoned it (2007) after rapid multi-organ cancers in rodents.** He dismisses this as an extreme-dose rodent artefact [paraphrase].
- **Regulatory:** FDA: not approved · WADA: **S4.4.1 (PPARδ agonists; GW1516 named)**, prohibited at all times · Israel: not verified.
- **Gap:** the developer stopped it over cancer; he calls that "the cancer lie".

#### **FOXO4-DRI**
- **Class:** D-retro-inverso senolytic peptide. Research compound. [literature]
- **Big Three (his framing):** **rejected by him.** Senescence sits under inflammation in his framework [inferred]; he says MOTS-c "works infinitely better" [v].
- **Verified quote:** "it's gimmicky, unnecessary and usually makes people sick" [v].
- **Real mechanism [literature]:** disrupts FOXO4–p53 binding, releasing p53 to trigger apoptosis in senescent cells (mouse).
- **Human evidence · grade:** mouse · **D**.
- **Key risks:** unknown; p53-driven apoptosis outside senescent cells.
- **Regulatory:** FDA: not approved · WADA: not named · Israel: not verified.
- **Gap:** his rejection fits the evidence, but the alternative he prefers (MOTS-c) is also grade D.

### 2.6 **Methylene blue** (methylthioninium chloride)

- **Class:** redox-cycling phenothiazine dye. **FDA-approved prescription drug** (ProvayBlue) for acquired methaemoglobinaemia only. It is separately sold as a non-pharmaceutical product, including by his company [corpus]. [literature]
- **Big Three assignment:** **ATP shortage** (electron-transport "bypass") plus **inflammation** (lower ROS → NF-κB, support for regulatory T cells). A third-party summary places it in a "Trilogy for Life" with BPC-157 and MOTS-c as the cognition leg. [his framing]
- **His framing:**
 - "It is an electron recycler." [v]
 - "This road just appears and you just go right around the traffic jam." [v]
 - "It's also a pretty solid MAO inhibitor ... that's just a side benefit not a side effect." [v]
 - "It's not a medicine." [v]
 - Video: "Methylene blue: is it a secret weapon for health" [v, title].
 - He cites cell and sleep studies with precise ATP, ROS and sleep percentages [paraphrase]; these were not verified.
- **Real mechanism (chain) [literature]:**
 1. **Methaemoglobin reduction** (the approved use): converted to leucomethylene blue, which turns methaemoglobin back into working haemoglobin.
 2. **Alternative electron carrier:** it accepts electrons from NADH and passes them directly to **cytochrome c**, raising **Complex IV** activity when the electron-transport chain is dysfunctional. A detour road around a jammed section of the conveyor belt.
 3. **Potent reversible MAO-A inhibitor.** This is the dominant safety fact, not a side note.
 4. Also inhibits **nitric oxide synthase** (the basis of its vasoplegia use) and several **CYP enzymes**.
 5. The response is **biphasic (hormetic)**: the redox benefit is confined to a narrow exposure window, and beyond it the effect turns pro-oxidant.
- **Body systems affected:** blood (methaemoglobin), mitochondria, brain (MAO-A, cognition), vasculature (NO).
- **Human evidence [literature]:**
 - Acquired methaemoglobinaemia: approved, labelled use.
 - Vasoplegia / septic shock: a single-centre RCT (n=91) showed faster vasopressor discontinuation; a meta-analysis of 6 RCTs (n=302) suggested lower short-term mortality. All low certainty.
 - Cognition: a small randomised neuroimaging study in healthy adults (n=26) found greater fMRI task responses and a 7% gain in correct memory-retrieval responses.
 - A methylene-blue derivative (LMTM, hydromethylthionine) missed its primary endpoints in two phase 3 Alzheimer's trials.
 - Neuroprotection (stroke, Alzheimer's, Parkinson's, TBI) and "ATP restoration" for fatigue: animal or cell work only.
- **Evidence grade:** **A** for acquired methaemoglobinaemia (labelled); **C** for vasoplegia (low certainty); **C/D** for cognition; **negative** for the derivative in Alzheimer's; **D** for fatigue, "mitochondrial repair" or neuroprotection.
- **Key risks:**
 - **Boxed warning: serotonin syndrome** with serotonergic drugs (SSRIs, SNRIs, other MAO inhibitors and other serotonergic medicines). Anyone on such a drug: do not add it; see the prescriber.
 - **G6PD deficiency:** haemolytic anaemia.
 - Contraindicated with severe hypersensitivity. Pregnancy: avoid; physician only.
 - CYP-inhibition interactions; interferes with pulse-oximetry readings; blue-green urine and skin discoloration; dizziness and confusion.
 - Non-pharmaceutical products: purity and strength unverified. Corpus reviews and his own rants describe pale, inconsistent or dye-adulterated products.
- **What he stacks it with:** MOTS-c, NAD+ (mitochondrial "power plant" rebuild); MOTS-c + Retatrutide (Kangaroo stack); BPC-157 + MOTS-c (the third-party "Trilogy for Life").
- **Regulatory:**
 - FDA: approved prescription drug (acquired methaemoglobinaemia only); every other use is off-label; non-pharmaceutical products are not approved drugs.
 - WADA: not named.
 - Israel: not verified.
 - Any use is a decision for a physician.
- **Gap:** He calls MAO-A inhibition "just a side benefit", yet it is the reason for a boxed warning. He says "it's not a medicine", yet it is an FDA-approved prescription drug. The mitochondrial detour is real biochemistry. The human benefit for fatigue or brain health is not shown, and a derivative failed in Alzheimer's.
 - בעברית: הוא קורא לעיכוב MAO-A "תועלת צדדית" — בפועל זו הסיבה לאזהרת הקופסה השחורה (תסמונת סרוטונין).

---

## 3. Longevity / circadian / neuro peptides

### 3.1 **Epitalon** (Epithalon, AEDG)

- **Class:** synthetic tetrapeptide (Ala-Glu-Asp-Gly) modelled on the bovine pineal extract Epithalamin. Research compound. [literature]
- **Big Three assignment:** framed as **anti-senescence / inflammation** ("stop their inflammatory temper tantrum" [v]), plus a circadian/HPA reset that fixes cortisol-driven blood sugar [paraphrase]. [his framing]
- **His framing:**
 - "It doesn't slow the clock. It winds it backwards." [v]
 - "A mechanic for your genes." [v]
 - "It increases the lifespan of rats by 12 to 13%." [v]
- **Real mechanism (chain) [literature]:**
 1. In vitro it upregulates **hTERT mRNA / telomerase**, re-extending the fuse on the stick of dynamite.
 2. That produces **telomere lengthening in cultured normal cells**.
 3. **In breast-cancer cell lines (2025) it also activated ALT** (alternative lengthening of telomeres), the same hotwire tumours use to never die.
 4. Other reports: melatonin restoration in old monkeys, IL-2 mRNA, antioxidant effects. A 2025 review: it "remains uncertain" whether these are the real mechanisms.
- **Body systems affected:** pineal/circadian system, immune cells, retina (rodent).
- **Human evidence [literature]:** almost entirely from one Russian group (Khavinson/Anisimov): a 266-person over-60 cohort reporting a 1.6–1.8× mortality reduction, and 79 coronary patients. Neither was randomised-blinded by modern standards or independently replicated.
- **Evidence grade: D.**
- **Key risks:**
 - **Telomerase and ALT activation are immortalisation mechanisms.** "Telomere lengthening" must never be presented as self-evidently good [literature].
 - Avoid with any cancer history or high cancer risk unless an oncologist is involved [inferred].
 - FDA: immunogenicity, aggregation, impurities, no safety data.
- **What he stacks it with:** BPC-157, MOTS-c, Thymosin α1 (the "four peptides for life" [v, title]); GHK-Cu + MOTS-c (anti-aging); DSIP (sleep stack).
- **Regulatory:**
 - FDA: removed from Category 2 in Apr 2026; PCAC recommended in Jul 2026 (non-binding).
 - WADA: not named (S0 catch-all [inferred]).
 - Israel: not verified.
- **Gap:** "Winds it backwards" [v] — rats plus one non-replicated research group. The headline mechanism is shared with cancer.
 - בעברית: "מחזיר את השעון אחורה" — אבל טלומראז ו-ALT הם בדיוק המנגנונים שסרטן משתמש בהם.

### 3.2 **DSIP** (delta sleep-inducing peptide, emideltide)

- **Class:** nonapeptide first isolated in 1977. Research compound. [literature]
- **Big Three assignment:** not cleanly mapped. He sells it as a "longevity molecule" [v, episode description] that repairs sleep, cortisol rhythm and HPTA. [his framing]
- **His framing:**
 - After first use: "mind blowing rest." [v]
 - It "fixes your circadian rhythm but it also recovers the cortisol issues" [v].
 - Not a sleep aid but a longevity peptide: video "DSIP: the masterclass on this longevity peptide" [v, title].
- **Real mechanism [literature]:** largely unresolved after four decades. Proposed: NMDA-receptor effects, MAPK interaction, homology to GILZ. **Blood-brain-barrier penetration is limited**, a basic problem for any peripheral use.
- **Body systems affected:** CNS sleep architecture (claimed).
- **Human evidence [literature]:** small 1980s–early-1990s European trials. The best-controlled (double-blind, n=16, 1992) found effects "weak" and "not likely to be of major therapeutic benefit".
- **Evidence grade: D** (old, small, inconsistent; the best trial was negative).
- **Key risks:** long-term safety never established. FDA flags immunogenicity and impurities. Do not combine with sedatives or alcohol without a physician [inferred].
- **What he stacks it with:** NAD+; MK-677; Epitalon (sleep-apnea stack).
- **Regulatory:**
 - FDA: removed from Category 2 in Apr 2026. **PCAC voted AGAINST Bulks-List inclusion (7–6) in Jul 2026** [reg-verified 2026-10-03].
 - WADA: not named.
 - Israel: not verified.
- **Gap:** "Longevity peptide" — even the 1990s sleep data were weak, and the FDA advisory panel turned it down.
 - בעברית: אפילו נתוני השינה מהניינטיז חלשים — וועדת ה-FDA דחתה אותו.

### 3.3 Neuro / anxiolytic research compounds he names (compact templated entries)

#### **Semax**
- **Class:** synthetic heptapeptide, ACTH(4-7)-Pro-Gly-Pro analog. Registered in Russia; research compound elsewhere. [literature]
- **Big Three (his framing):** not assigned to an axis; neuroprotection (BDNF/NGF) for dementia, Alzheimer's, Parkinson's and MS [paraphrase].
- **Verified quote:** "Semax is killer" [v].
- **Real mechanism [literature]:** ↑BDNF/TrkB signalling in rodents; melanocortin-derived fragment.
- **Human evidence · grade:** registered in Russia (stroke/cognition); small Russian trials · **C/D**.
- **Key risks:** little independent data; unapproved product identity.
- **Regulatory:** FDA: removed from Cat 2 Apr 2026; PCAC recommended Jul 2026 (non-binding) · WADA: not named · Israel: not verified.
- **Gap:** no independent RCT for any of the dementia or Parkinson's claims.

#### **Selank**
- **Class:** synthetic tuftsin-analog heptapeptide. Registered in Russia as an anxiolytic. [literature]
- **Big Three (his framing):** **inflammation**; anxiety framed as an amygdala → cortisol loop with failed "GABA brakes" and neuroinflammation [paraphrase].
- **Verified quote:** chapter "Selank rebuilds the brain" [v, title].
- **Real mechanism [literature]:** GABA-A modulation, enkephalinase effects (animal).
- **Human evidence · grade:** registered in Russia as an anxiolytic; small Russian trials · **C/D**.
- **Key risks:** little independent data; additive effects with other sedating or anxiolytic drugs [inferred]: physician only.
- **Regulatory:** FDA: withdrawn-nomination table · WADA: not named · Israel: not verified.
- **Gap:** "Rebuilds the brain" has no imaging or independent RCT behind it.

#### **Cerebrolysin**
- **Class:** porcine brain-derived peptide mixture. Approved in several countries outside the US. [literature]
- **Big Three (his framing):** not assigned; neurotrophic "brain protector" for dementia, MS, Parkinson's, ADHD, tinnitus [paraphrase].
- **Verified quote:** chapter "Cerebrolysin the ultimate brain protector" [v, title].
- **Real mechanism [literature]:** peptide mixture with neurotrophic-like activity.
- **Human evidence · grade:** Cochrane (acute ischaemic stroke): **no mortality benefit, possible excess of non-fatal serious adverse events** · **A-negative** (stroke mortality), **C** (function).
- **Key risks:** allergy, seizures; animal-derived product.
- **Regulatory:** FDA: not US-approved (approved in several other countries) · WADA: not named · Israel: not verified.
- **Gap:** he calls it "the ultimate brain protector", but a Cochrane review found no mortality benefit and a possible harm signal.

#### **Dihexa**
- **Class:** angiotensin-IV-derived small peptide mimetic. Research compound. [literature]
- **Big Three (his framing):** not assigned; neurotrophic, ranked below Semax.
- **Verified quote:** "not nearly as well as Semax" [v].
- **Real mechanism [literature]:** **HGF/c-Met** potentiator.
- **Human evidence · grade:** rodent only · **D**.
- **Key risks:** **c-Met is an oncogenic pathway** (double edge).
- **Regulatory:** FDA: removed from Cat 2 Apr 2026 · WADA: not named · Israel: not verified.
- **Gap:** no human data at all, acting on a cancer-growth pathway.

#### **Aniracetam** (+ racetams)
- **Class:** racetam nootropic; AMPA-receptor positive allosteric modulator. Not FDA-approved; sold by his company as a "research" nootropic [corpus]. [literature]
- **Big Three (his framing):** **inflammation** (he says it reduces neuroinflammation), for anxiety and brain fog; part of a "Limitless" stack with Selank [paraphrase].
- **Verified quote:** chapter "Aniracetam Selank synergy" [v, title].
- **Real mechanism [literature]:** AMPA-receptor positive allosteric modulator.
- **Human evidence · grade:** old small dementia trials · **C/D**. No controlled anxiety trial.
- **Key risks:** CNS effects; unregulated quality.
- **Regulatory:** FDA: not approved · WADA: not named · Israel: not verified.
- **Gap:** sold for anxiety with no anxiety RCT; the old trials were in dementia.

### 3.4 **Nicotine** (pharmaceutical nicotine, outside tobacco)

- **Class:** alkaloid; nicotinic acetylcholine receptor (nAChR) agonist. Approved as nicotine replacement therapy (NRT) for smoking cessation. [literature]
- **Big Three assignment:** **inflammation** (an α7-nAChR cholinergic anti-inflammatory framing: less NF-κB, TNF-α, IL-6, IL-1β) and neuroprotection; he adds sirtuin/mitochondrial effects (ATP). [his framing]
- **His framing:**
 - "Is nicotine addictive (Absolutely not)" [v, caption].
 - "It's not addictive in its nutrient form." [v]
 - A "therapeutic nutrient" [v, episode description]; chapter "Nicotine, the misunderstood ally" [v, title].
 - "As a standalone it's not what you think it is." [v]
 - Uses claimed: Parkinson's, Alzheimer's/dementia, Hashimoto's, eczema, parasites, cancer adjunct, COVID, arrhythmia (with BPC-157 and thymosin α1) [paraphrase]. He cites cognitive-score percentages from named papers [paraphrase]; not verified.
- **Real mechanism (chain) [literature]:**
 1. Binds **nAChRs**. At **α4β2** receptors in the brain's reward circuit it releases **dopamine**: the doorbell that also rings the reward bell, which is the engine of dependence.
 2. At **α7** receptors on neurons it supports attention and some memory signalling.
 3. α7 on macrophages takes part in the vagal **cholinergic anti-inflammatory pathway**: the vagus nerve tells immune cells to turn the cytokine tap down (animal models).
 4. Sustained exposure **desensitises** nicotinic receptors.
 5. Sympathetic activation raises **heart rate and blood pressure**; nicotine also reduces insulin sensitivity [literature].
- **Body systems affected:** brain (reward, attention), autonomic nervous system, heart and vessels, immune cells, glucose metabolism.
- **Human evidence [literature]:**
 - Smoking cessation (NRT): approved, large RCT evidence.
 - Mild cognitive impairment: a small pilot RCT (n=74) improved attention and some memory measures; confirmation in a larger trial is still needed [inferred].
 - Early Parkinson's: **NIC-PD (n=163) did not slow progression.**
 - Active ulcerative colitis: better than placebo for inducing remission, not better than standard therapy, with more side effects (Cochrane).
 - Hashimoto's, eczema, parasites, cancer, COVID, arrhythmia: no supporting trials.
- **Evidence grade:** **A** for smoking cessation; **C** for attention in MCI; **negative** for Parkinson's progression; **C** for ulcerative colitis (inferior to standard care); **D** for anti-inflammatory, autoimmune or longevity claims.
- **Key risks:**
 - **Dependence.** Nicotine is the main dependence-producing constituent of tobacco [literature]. His "absolutely not" is false.
 - **Heart:** ↑heart rate and blood pressure. The NRT label tells people with heart disease, a recent heart attack or an irregular heartbeat to ask a doctor first. That is the opposite of his arrhythmia anecdote.
 - **Glucose:** reduces insulin sensitivity, working against his own Big Three goal.
 - **Pregnancy and adolescence:** harms fetal and adolescent brain development [literature].
 - Sleep disturbance, nausea, local irritation; poisoning risk for children and pets.
- **What he stacks it with:** BPC-157 + Thymosin α1 (arrhythmia anecdote); nootropic stacks.
- **Regulatory:**
 - FDA: approved for smoking cessation only; every other use is off-label.
 - WADA: **2026 Monitoring Program, not prohibited** [corpus, WADA 2026].
 - Israel: NRT products likely available in pharmacies [inferred]; not verified.
 - Any use outside smoking cessation is a decision for a physician.
- **Gap:** "Absolutely not" addictive — nicotine is the addictive part of tobacco, and the one rigorous disease-modification trial (Parkinson's) was negative.
 - בעברית: "בכלל לא ממכר" — ניקוטין הוא בדיוק הרכיב הממכר בטבק, והניסוי הרציני בפרקינסון נכשל.

---

## 4. Hormone-axis peptides (sex hormones and GH)

### 4.1 **Kisspeptin-10**

- **Class:** endogenous neuropeptide fragment; KISS1R agonist. Investigational. [literature]
- **Big Three assignment:** sits **outside** the Big Three as the hormone director. He links menopause and low testosterone back to all three. [his framing]
- **His framing:**
 - "...upstream signal. It forces the hypothalamus to release GnRH." [v]
 - His own caution: "gently reawaken your pituitary." [v]
 - Claims an "80% reduction in hot flashes" [v] and restored cycles in perimenopause [paraphrase]. **No published trial.**
- **Real mechanism (chain) [literature]:** this is the best-validated mechanism in the whole set.
 1. Binds **KISS1R (GPR54)** on hypothalamic **GnRH neurons**, the ignition switch on the hormone engine.
 2. That produces a **GnRH pulse**.
 3. Then **LH/FSH**, then **testosterone/estradiol**.
 4. Arcuate **KNDy neurons** drive the pulses (the drummer setting the beat).
 5. A single acute exposure gives an immediate LH pulse and *resets* the pulse generator.
 6. **Continuous or chronic exposure DESENSITISES the receptor and suppresses the axis**: hold the ignition key down and you burn out the starter.
- **Body systems affected:** hypothalamic-pituitary-gonadal axis; possibly a direct intratesticular effect (monkey).
- **Human evidence [literature]:**
 - Reproducible acute pharmacodynamics: LH pulses in men; sexually dimorphic in women.
 - Kisspeptin-54 investigated for hypothalamic amenorrhoea and as an IVF trigger.
 - In a controlled human study (n=95), biologically active kisspeptin did not change cortisol, BP, heart rate or anxiety.
 - The validated KNDy-pathway hot-flash drugs are **NK3R antagonists (fezolinetant, elinzanetant; phase 3 RCTs)**, which he dismisses.
- **Evidence grade:** **B** as an acute endocrine probe; **D** as a therapy (no chronic-use safety data).
- **Key risks:** the paradoxical shutdown of the axis it is meant to "restart" [literature]; fertility consequences; hormone-sensitive cancers (breast, prostate, endometrium) [inferred]. Physician/endocrinologist only.
- **What he stacks it with:** Enclomiphene, hCG, CJC-1295 + Ipamorelin (the "TRT off ramp" [v, title]); estradiol, NAD+, MOTS-c (menopause); pregnenolone.
- **Regulatory:**
 - FDA: **ACTIVE Category 2 (503A, since 29 Sep 2023)**, i.e. flagged as a significant safety risk for compounding.
 - WADA: **S2.2.1 (testosterone-stimulating peptides in males — prohibited in males)**.
 - Israel: not verified.
- **Gap:** The mechanism is real, but chronic exposure is expected to *suppress* the very axis he wants to restart, and his hot-flash numbers have no trial behind them.
 - בעברית: המנגנון אמיתי — אבל חשיפה כרונית צפויה לכבות את הציר שהוא מבטיח "להדליק".

### 4.2 **CJC-1295** (with/without DAC; "Mod GRF 1-29")

- **Class:** GHRH analog. Research compound. [literature]
- **Big Three assignment:** **insulin resistance / muscle-as-metabolic-organ**; age reversal. [his framing]
- **His framing:**
 - "CJC 1295 is not the hormone, it's the signal. It tickles the pituitary." [v]
 - "CJC fills the reservoir." [v]
 - Restores "the GH axis of a 25 year old." [v]
 - Claims "zero increased cancer incidents" [v].
- **Real mechanism (chain) [literature]:**
 1. Binds the **GHRH receptor on pituitary somatotrophs**, pushing the button on the GH factory floor.
 2. That raises **GH pulse amplitude**.
 3. The liver then makes **IGF-1**, shipping the "build" work order to muscle and bone.
 4. The **DAC** version binds serum albumin and rides the albumin bus, giving prolonged action.
 5. A proper placebo-controlled pharmacology RCT in healthy adults showed dose-dependent rises in GH and IGF-1.
- **Body systems affected:** pituitary, liver, muscle, adipose tissue, glucose metabolism.
- **Human evidence:** a PK/PD RCT only. **No human outcome trial** for body composition, recovery, sleep or longevity.
- **Evidence grade:** **B** for raising GH/IGF-1 (a surrogate); **D** for any health outcome.
- **Key risks:**
 - FDA: **increased heart rate and systemic vasodilatory reactions**.
 - GH/IGF-1 class effects: **glucose intolerance / insulin resistance**, fluid retention, carpal tunnel, arthralgia, theoretical malignancy promotion.
 - Geroscience generally treats **higher IGF-1 as pro-ageing**. Double edge.
 - Not with active cancer, diabetic retinopathy or pregnancy [inferred from the GH-class label].
- **What he stacks it with:** Ipamorelin, Tesamorelin; nutrient cofactors; RU58841 (hair).
- **Regulatory:**
 - FDA: withdrawn-nomination table (page of 22 Apr 2026).
 - WADA: **S2.2.4**.
 - Israel: not verified.
- **Gap:** It reliably raises a lab number (IGF-1). Nobody has shown that number makes a person younger, and in ageing biology it may do the opposite.
 - בעברית: הוא מעלה מספר במעבדה (IGF-1) — אף אחד לא הראה שזה מצעיר, ובביולוגיה של הזדקנות אולי ההפך.

### 4.3 **Ipamorelin**

- **Class:** selective ghrelin-receptor (GHSR-1a) agonist pentapeptide. Research compound. [literature]
- **Big Three assignment:** same as CJC (muscle, metabolism, GH axis); he also claims a thyroid (TRH/T3) effect [paraphrase]. [his framing]
- **His framing:**
 - "It hits GH release button, nothing else." [v]
 - "The secret sauce of this entire thing." [v]
 - "Ipamorelin opens the gate, floods the system." [v]
- **Real mechanism (chain) [literature]:**
 1. Binds the **ghrelin receptor** on the pituitary: a second key to the same factory door.
 2. That releases GH via a pathway parallel to GHRH, functionally opposing **somatostatin** (taking a foot off the brake).
 3. It is relatively selective, with little ACTH/cortisol or prolactin release.
 4. Combined with GHRH analogs, the GH pulse is larger.
- **Body systems affected:** pituitary, liver (IGF-1), GI motility.
- **Human evidence:** its only sizeable efficacy RCT (post-operative ileus, phase 2, n=114) **missed its endpoint**.
- **Evidence grade: D** for any wellness outcome.
- **Key risks:** FDA cites a **reported death in a gastric-motility study**; GH-axis class risks as for CJC-1295.
- **What he stacks it with:** CJC-1295, Tesamorelin.
- **Regulatory:**
 - FDA: **ACTIVE Category 2 (503B)**.
 - WADA: **S2.2.4**.
 - Israel: not verified.
- **Gap:** "The secret sauce" failed its only real trial, and FDA has it on the active safety-risk list.
 - בעברית: "הרוטב הסודי" נכשל בניסוי האמיתי היחיד שלו, וה-FDA מחזיק אותו ברשימת סיכון פעילה.

### 4.4 **Tesamorelin** (Egrifta SV / Egrifta WR)

- **Class:** stabilised GHRH(1-44) analog. **FDA-approved prescription drug.** [literature]
- **Big Three assignment:** **insulin resistance / visceral fat** ("the dangerous fat that wraps up your organs" [v]), plus muscle preservation on GLP-1-class drugs. [his framing]
- **His framing:**
 - "Brutally effective at visceral fat loss." [v]
 - "Zero association between IGF-1 levels and cancer incidence." [v]
 - A cancer-rate comparison from the HIV trials (unverified figures) [paraphrase].
- **Real mechanism (chain) [literature]:**
 1. Binds the **GHRH receptor** (same receptor as CJC-1295; the difference is that this one finished the approval pathway).
 2. That produces a **pulsatile endogenous GH** pulse.
 3. GH drives **lipolysis** in visceral fat, opening the warehouse around the organs.
 4. **IGF-1 ↑** in the liver.
- **Body systems affected:** visceral adipose tissue, liver fat, glucose metabolism, joints and nerves (side effects).
- **Human evidence [literature]:**
 - Phase 3 in HIV lipodystrophy (n=410 across arms): **VAT −27 cm² vs +4 cm²** with placebo; about 18% VAT reduction sustained at 12 months; **regain on stopping**.
 - HIV-associated NAFLD RCT (n=61): hepatic fat fraction −37% relative.
 - **No general-population or anti-aging data.**
- **Evidence grade:** **A** for visceral fat in HIV lipodystrophy; **D** for general fat loss, "GH optimisation" or recovery.
- **Key risks (label):**
 - Contraindicated with disrupted hypothalamic-pituitary axis, **active malignancy**, pregnancy, or hypersensitivity.
 - **HbA1c ≥6.5% developed in 5% vs 1%**; fluid retention, arthralgia, carpal tunnel; hypersensitivity; injection-site reactions.
 - The label calls for **IGF-1 monitoring by the prescriber**. Rule for the agent: *if IGF-1 or HbA1c rises, do not change the dose yourself — contact the prescribing physician, who monitors IGF-1 and decides any change.*
- **What he stacks it with:** Retatrutide (+ 5-Amino-1MQ, the "nuclear option" [v, title]); Ipamorelin, CJC-1295.
- **Regulatory:**
 - FDA: approved (HIV lipodystrophy only).
 - WADA: **S2.2.4**.
 - Israel: not verified.
- **Gap:** A real drug with real data, but only for HIV lipodystrophy. Off-label "recomposition" stacking with an unapproved triple agonist has no data.
 - בעברית: תרופה אמיתית עם נתונים אמיתיים — אבל רק לליפודיסטרופיה ב-HIV.

### 4.5 Other GH / sex-axis compounds he names (compact templated entries)

#### **MK-677** (ibutamoren)
- **Class:** non-peptide ghrelin-receptor (GHSR-1a) agonist. Research compound. [literature]
- **Big Three (his framing):** **insulin resistance / lean tissue** via the GH axis ("restore growth hormone and a lot of the lean tissue" [v]).
- **Verified quote:** chapter "MK 677 the odd cousin" [v, title]; "non negotiable" [v] in a longevity stack; "infinitely better than Hexa and Serma and Tessa" [v].
- **Real mechanism [literature]:** ghrelin-receptor agonist → GH/IGF-1; ↑appetite (ghrelin mimetic).
- **Human evidence · grade:** placebo-controlled RCT in older adults: ↑IGF-1, ↑fat-free mass, but **↑fasting glucose and insulin resistance**, ↑appetite, oedema; a hip-fracture trial raised a heart-failure signal · **B** surrogate / **D** outcomes.
- **Key risks:** glucose; fluid; heart failure.
- **Regulatory:** FDA: **active Cat 2 (503B)** · WADA: S2.2.4 · Israel: not verified.
- **Gap:** "non negotiable" for longevity, yet its best trial worsened insulin resistance, the very failure he says he is fixing.

#### **AOD-9604**
- **Class:** modified hGH fragment 177-191. Research compound. [literature]
- **Big Three (his framing):** **insulin resistance / visceral fat**, plus joints; claims it rebuilds cartilage [paraphrase].
- **Verified quote:** video "The secret about AOD9604 they're hiding" [v, title].
- **Real mechanism [literature]:** lipolytic GH fragment without an IGF-1 rise.
- **Human evidence · grade:** **phase 2b obesity trial failed** · **negative/D**. Cartilage: no human data.
- **Key risks:** little long-term data.
- **Regulatory:** FDA: withdrawn-nomination table · WADA: S2.2.3 (named GH fragment) · Israel: not verified.
- **Gap:** the fat-loss trial failed and the cartilage claim has no human trial.

#### **IGF-1 LR3**
- **Class:** IGF-1 analog with reduced IGFBP binding (longer action). Research compound. [literature]
- **Big Three (his framing):** none stated by him; a listed product [corpus].
- **Verified quote:** no verbatim quote from him found.
- **Real mechanism [literature]:** IGF-1 receptor agonist; reduced IGFBP binding raises free activity.
- **Human evidence · grade:** none · **D**.
- **Key risks:** **hypoglycaemia**; IGF-1 growth/cancer concerns.
- **Regulatory:** FDA: not approved · WADA: **S2.3** (IGF-1 analogues) · Israel: not verified.
- **Gap:** sold with zero human data while acting like insulin.

#### **SARMs** (ostarine, LGD-4033, RAD-140, YK-11)
- **Class:** tissue-selective androgen-receptor agonists. Research chemicals, sold by his company [corpus]. [literature]
- **Big Three (his framing):** not assigned; muscle preservation framed as metabolic protection [paraphrase].
- **Verified quote:** the "'god mode' stack" [v, title]. His needle-free framing for this stack is [paraphrase].
- **Real mechanism [literature]:** tissue-selective androgen-receptor agonists.
- **Human evidence · grade:** Ostarine: phase 2 cachexia lean-mass gain, but **phase 3 function endpoints failed**; LGD-4033: small RCT ↑lean mass, ↓HDL, ↓testosterone · **B** surrogate / **D** outcomes.
- **Key risks:** **drug-induced liver injury**, HDL suppression, HPG shutdown.
- **Regulatory:** FDA: not approved · WADA: **S1.2** · Israel: not verified.
- **Gap:** lean-mass gains on a scan, but function trials failed and the liver signal is real.

#### **PT-141** (bremelanotide, Vyleesi)
- **Class:** cyclic heptapeptide MC4R agonist. **Approved (2019)** for premenopausal HSDD. [literature]
- **Big Three (his framing):** none; libido [paraphrase].
- **Verified quote:** no verbatim quote from him found.
- **Real mechanism [literature]:** MC4R agonist in the CNS.
- **Human evidence · grade:** modest effect in phase 3 · **A-narrow**.
- **Key risks:** nausea, transient BP rise, focal hyperpigmentation; contraindicated with uncontrolled hypertension / CVD.
- **Regulatory:** FDA: approved (narrow) · WADA: not prohibited · Israel: not verified.
- **Gap:** the approved product has a narrow indication; a "research" vial is not that product [inferred].

#### **Melanotan II**
- **Class:** non-selective melanocortin (MC1–5) agonist. Research compound. [literature]
- **Big Three (his framing):** **all three** (inflammation control, insulin resistance, mitochondrial function), plus ED [paraphrase].
- **Verified quote:** video "Melanotan 2 masterclass" [v, title].
- **Real mechanism [literature]:** non-selective MC1–5 agonist.
- **Human evidence · grade:** none controlled · **D**.
- **Key risks:** FDA notes **melanoma, PRES**; case reports of changing nevi, rhabdomyolysis, priapism.
- **Regulatory:** FDA: removed from Cat 2 Apr 2026 · WADA: S0 catch-all [inferred] · Israel: not verified.
- **Gap:** no controlled human data, and a melanoma signal.

#### **Exogenous HGH** (somatropin)
- **Class:** recombinant growth hormone. Prescription drug. [literature]
- **Big Three (his framing):** **argued against** as a fix for the GH axis.
- **Verified quote:** "It's a wrecking ball" [v]; "shuts down natural production" [v].
- **Real mechanism [literature]:** exogenous GH; negative feedback suppresses endogenous GH.
- **Human evidence · grade:** approved for GH deficiency and other labelled indications · **A** (labelled uses).
- **Key risks:** his direction on feedback is right; his percentages are unverified. GH-class risks (glucose, fluid, joint pain, carpal tunnel).
- **Regulatory:** FDA: Rx only · WADA: S2.2.3 · Israel: not verified.
- **Gap:** he is broadly right about unsupervised GH, but the secretagogues he prefers carry the same GH/IGF-1 risks.

#### **Sermorelin**
- **Class:** GHRH(1-29). [literature]
- **Big Three (his framing):** **rejected**.
- **Verified quote:** "it's garbage" [v] (said of sermorelin and semaglutide).
- **Real mechanism [literature]:** GHRH-receptor agonist.
- **Human evidence · grade:** formerly FDA-approved (Geref), commercially discontinued · **B/C**.
- **Key risks:** GH-class risks.
- **Regulatory:** FDA: no marketed approved product · WADA: S2.2.4 · Israel: not verified.
- **Gap:** he rejects sermorelin yet promotes CJC-1295, a modified analog acting at the same receptor.

---

## 5. GLP-1-class drugs

### 5.1 **Semaglutide** (Ozempic, Wegovy, Rybelsus)

- **Class:** GLP-1 receptor agonist. **Approved prescription drug.** [literature]
- **Big Three assignment:** he concedes it touches insulin resistance and visceral fat but calls it inferior ("entry point" [v]). [his framing]
- **His framing:**
 - "GLP 1 receptor agonist, nothing more." [v]
 - "An appetite suppressant with some slick marketing." [v]
 - "Sarcopenia 100% of the time" [v]; "70 plus percent" of the weight lost was "muscle, connective tissue, bone" [v]. **Contradicted by data.**
- **Real mechanism (chain) [literature]:**
 1. **GLP-1R on pancreatic β-cells** → glucose-dependent insulin release: insulin only when there is glucose at the door.
 2. **α-cell glucagon ↓**: the liver stops dumping sugar.
 3. **Hypothalamic and brainstem appetite circuits** → less intake: turns down the hunger radio.
 4. **Slowed gastric emptying**: the drain out of the stomach narrows. This is both a satiety mechanism and the source of its GI and aspiration risks.
- **Body systems affected:** pancreas, brain appetite centres, GI tract, cardiovascular system, kidney, liver (MASH).
- **Human evidence [literature]:**
 - **STEP 1** (n=1,961, 68 weeks): **−14.9% vs −2.4%**. **STEP 4:** regain on withdrawal (it is chronic therapy).
 - **SELECT** (n=17,604, CVD + overweight, no diabetes): **MACE HR 0.80**; kidney composite HR 0.78.
 - Labelled for CV risk reduction, chronic weight management (≥12 years) and noncirrhotic MASH F2–F3.
 - DEXA substudies: roughly **25–40% of lost weight is lean mass** (including water and organ mass), not 70%.
 - **Brain:** semaglutide in early Alzheimer's (**EVOKE/EVOKE+, n=3,808**) **did not slow progression** on CDR-SB [reg-verified 2026-10-03].
- **Evidence grade: A** (hard cardiovascular outcomes); **negative** for Alzheimer's progression.
- **Key risks (label) [literature]:**
 - **Boxed warning:** thyroid C-cell tumours in rodents. **Contraindicated with personal/family history of medullary thyroid carcinoma or MEN 2.**
 - Acute pancreatitis, gallbladder disease, **AKI from dehydration**, severe GI reactions (not for severe gastroparesis), hypersensitivity, diabetic-retinopathy complications, heart-rate increase, suicidal-ideation monitoring.
 - **Pulmonary aspiration under anaesthesia/sedation**: tell the anaesthetist.
 - **Hypoglycaemia with insulin/sulfonylureas.**
 - Pregnancy.
- **What he stacks it with:** none. He calls it "garbage" [v] and opposes stacking it with retatrutide. He compares it with MOTS-c in one video.
- **Regulatory:**
 - FDA: approved.
 - WADA: not prohibited.
 - **Israel [reg-verified 2026-10-03]:** Ozempic registered for T2D, and the MoH barred its sale for weight loss in Apr 2024. Wegovy registered and marketed since Apr 2024. 2026 basket reportedly adds Wegovy for ages 12–18 [news reports only; verify].
- **Gap:** He calls the drug with the strongest hard-outcome data in this whole file "garbage", while borrowing its trials (SELECT, FLOW) to promote retatrutide.
 - בעברית: הוא קורא "זבל" לתרופה עם הנתונים הקשים החזקים ביותר בקובץ, ובו בזמן "שואל" את הניסויים שלה לטובת רטטרוטייד.

### 5.2 **Tirzepatide** (Mounjaro, Zepbound)

- **Class:** dual GIP + GLP-1 receptor agonist. **Approved prescription drug.** [literature]
- **Big Three assignment:** insulin resistance; he frames GIP as the fat-storage "off switch". [his framing]
- **His framing:**
 - "GIP is actually the main attraction." [v]
 - "GIP hammers the off switch" on fat storage [v].
 - Elsewhere he groups it with semaglutide: "they're garbage" [v].
- **Real mechanism (chain) [literature]:**
 1. **GLP-1R arm:** same as semaglutide (insulin, glucagon, appetite, gastric emptying).
 2. **GIP-receptor arm:** added insulin sensitisation and appetite/energy-balance effects, and adipose nutrient handling (the warehouse manager deciding what gets shelved).
- **Body systems affected:** pancreas, adipose tissue, brain, GI tract, upper airway (OSA indication).
- **Human evidence [literature]:**
 - **SURMOUNT-1** (n=2,539, 72 weeks): **−15.0% to −20.9% across dose arms vs −3.1%**.
 - 176-week prediabetes cohort: progression to T2D **1.3% vs 13.3% (HR 0.07)**.
 - DXA: about **75% fat / 25% lean**, the same proportion as placebo.
 - Approved for moderate-to-severe OSA with obesity.
- **Evidence grade: A.**
- **Key risks:** class label as for semaglutide (MTC/MEN 2 contraindication, pancreatitis, gallbladder, AKI, severe GI, retinopathy, hypoglycaemia with secretagogues/insulin, aspiration). Oral contraceptives may be less effective during GI slowing; the label advises discussing contraception with the physician.
- **What he stacks it with:** none. He discusses switching to retatrutide.
- **Regulatory:**
 - FDA: approved.
 - WADA: not prohibited.
 - **Israel:** Mounjaro marketed since Sep 2024; not in the public basket as of reports seen [reg-verified 2026-10-03 for marketing; basket status from news reports only — verify current basket].
- **Gap:** The "muscle wasting" story is refuted by its own DXA data, where the lean/fat ratio matches ordinary weight loss.
 - בעברית: סיפור "שריפת השריר" נסתר בנתוני ה-DXA שלה עצמה.

### 5.3 **Retatrutide** (LY3437943)

- **Class:** GIP + GLP-1 + **glucagon** receptor triple agonist. **Investigational and approved nowhere.** Sold by his company (EliteBiogenix) as a research peptide. [literature / corpus]
- **Big Three assignment:** **all three simultaneously**; with MOTS-c, "they hit all three biological failures" [v]. [his framing]
- **His framing:**
 - "It's not a weight loss peptide... it's a hepatic metabolic reset device." [v]
 - "Arguably the most effective peptide on the planet." [v]
 - If it fails, "your biology is not working" [v].
 - "The only contra contraindication is if you can't control yourself." [v] **False.**
- **Real mechanism (chain) [literature]:**
 1. **GLP-1R:** insulin when glucose is present, less appetite, slower stomach.
 2. **GIP-R:** insulin sensitisation and adipose handling.
 3. **Glucagon-R (the novel arm):** **hepatic fat mobilisation and oxidation, ↑energy expenditure**. Glucagon opens the warehouse doors and makes the liver burn its own inventory.
 4. Net effect: large weight loss and very large liver-fat reductions.
- **Body systems affected:** liver, adipose tissue, pancreas, brain, heart rate/cardiovascular system, gallbladder.
- **Human evidence [literature; reg-verified 2026-10-03]:**
 - Phase 2 obesity (n=338, 48 weeks): up to about **−24% vs −2.1%**. MASLD substudy: liver fat −81–82% relative at 24 weeks.
 - **Phase 3 TRIUMPH-2 (T2D) and TRIUMPH-3 (severe obesity + CVD), topline 23 Jul 2026:** up to **−20.8%** and **−22.6%** at 80 weeks; improved TG, non-HDL, SBP and hsCRP. These are press-release toplines, not yet peer-reviewed.
 - **FDA submission planned for early 2027.**
 - His citations repeatedly **misattribute** tirzepatide (SURMOUNT) and semaglutide (SELECT, FLOW) trials to retatrutide.
- **Evidence grade:** **B** for weight and liver-fat surrogates, moving toward A once phase 3 is published and reviewed. No hard-outcome or long-term safety data yet.
- **Key risks:**
 - Dose-dependent **heart-rate increase**; GI effects; expected class risks (pancreatitis, gallbladder, MTC/MEN 2 caution, AKI, aspiration).
 - **Grey-market product of unverified identity:** a 2026 health-department alert in Victoria, Australia, reported at least 6 cases of acute liver injury after people took products labelled as retatrutide. Eli Lilly has filed lawsuits against sellers.
 - **Hypoglycaemia with insulin/sulfonylureas.** He himself warns "it will tank your blood sugar if you're already on insulin or metformin" [v]. He follows this with medication-adjustment advice that this file does not reproduce: any change to a glucose-lowering drug is the prescriber's decision.
 - Pregnancy.
 - Agent rule: **no self-titration of any kind. Any symptom, abnormal liver enzyme or heart-rate change: stop and see the physician.**
- **What he stacks it with:** MOTS-c, Tesamorelin, 5-Amino-1MQ, BPC-157, KPV, NAD+, methylene blue, SS-31, MK-677, GHK-Cu, Cardarine.
- **Regulatory:**
 - FDA: not approved (investigational); not on the Category pages.
 - WADA: unapproved, so falls under the S0 catch-all [inferred].
 - Israel: not registered (investigational globally).
- **Gap:** The molecule is genuinely powerful in trials. What he sells is an unapproved vial of unverified identity, promoted with other drugs' trial results and no contraindication list.
 - בעברית: המולקולה חזקה באמת בניסויים — אבל מה שנמכר הוא בקבוקון לא מאושר בלי זהות מאומתת.

### 5.4 Appetite / weight research compound (compact templated entry)

#### **Tesofensine**
- **Class:** serotonin–noradrenaline–dopamine reuptake inhibitor. Investigational; listed by his company as a research nootropic [corpus]. [literature]
- **Big Three (his framing):** **insulin resistance / appetite**. He contrasts its brain appetite target with retatrutide's metabolic target. Elsewhere he warns against unverified limitless pills [paraphrase].
- **Verified quote:** chapter "Tesofensine the triple reuptake inhibitor" [v, title].
- **Real mechanism [literature]:** triple monoamine reuptake inhibition → appetite suppression.
- **Human evidence · grade:** phase 2 RCT (n=203), meaningful weight loss · **B**.
- **Key risks:** **↑heart rate and BP**, mood/psychiatric effects, insomnia.
- **Regulatory:** FDA: not approved · WADA: not verified · Israel: not verified.
- **Gap:** a stimulant-like drug with cardiovascular and psychiatric effects, sold as a research chemical.

---

## 6. Master regulatory table (as of 2026-10-03)

*Israel column: the MoH registry was unavailable. Every "not verified" means unknown, not "not registered".*

| Compound | FDA status | FDA compounding list | WADA 2026 | Israel MoH |
|---|---|---|---|---|
| BPC-157 | Not approved | Removed from Cat 2 (Apr 2026); PCAC yes 8–6 (Jul 2026) | S0 (named) | Not verified / not known registered |
| TB-500 / Tβ4 | Not approved | Removed from Cat 2; PCAC yes | S2.3 (named) | Not verified |
| MOTS-c | Not approved | Removed from Cat 2; PCAC yes 7–5 | S4.4.1 (named) | Not verified |
| SS-31 / elamipretide | **Approved** (Forzinity, Barth, accelerated, Sep 2025) | n/a | Not named | Not verified |
| Epitalon | Not approved | Removed from Cat 2; PCAC yes | Not named (S0 [inferred]) | Not verified |
| Thymosin α1 | Not approved (US); approved in ~35 countries | Withdrawn-nomination table | Not named | Not verified |
| GHK-Cu | Cosmetic (topical); injectable unapproved | Injectable removed from Cat 2 | Not named | Topical likely available [inferred]; injectable not verified |
| KPV | Not approved | Removed from Cat 2; PCAC yes | Not named (S0 [inferred]) | Not verified |
| DSIP | Not approved | Removed from Cat 2; **PCAC NO 7–6** | Not named | Not verified |
| Kisspeptin-10 | Not approved | **ACTIVE Cat 2 (503A)** | S2.2.1 (testosterone-stimulating peptides in males — prohibited in males) | Not verified |
| CJC-1295 | Not approved | Withdrawn-nomination table | S2.2.4 | Not verified |
| Ipamorelin | Not approved | **ACTIVE Cat 2 (503B)** | S2.2.4 | Not verified |
| Tesamorelin | **Approved** (HIV lipodystrophy) | n/a | S2.2.4 | Not verified |
| 5-Amino-1MQ | Not approved | Not listed (corpus check) | Not named (S0 [inferred]) | Not verified |
| NAD+ (injectable) | Not an approved drug; compounded | Not listed | Not named | Not verified |
| NMN (oral) | **Lawful supplement ingredient** (FDA letters 29 Sep 2025) | n/a | Not named | Not verified |
| Methylene blue | **Approved** (acquired methaemoglobinaemia only) | n/a | Not named | Not verified |
| SR9009 | Not approved | Not listed | **S4.4.1 (Rev-erb agonists), prohibited at all times** | Not verified |
| Cardarine (GW1516) | Not approved | Not listed | **S4.4.1 (PPARδ agonists), prohibited at all times** | Not verified |
| Nicotine | **Approved** (smoking cessation only) | n/a | Monitoring Program, not prohibited | Not verified |
| Semaglutide | **Approved** | n/a | Not prohibited | **Registered** (Ozempic T2D; Wegovy obesity) |
| Tirzepatide | **Approved** | n/a | Not prohibited | **Registered/marketed** (Mounjaro) |
| Retatrutide | **Investigational**; FDA filing planned early 2027 | Not listed | S0 catch-all [inferred] | Not registered |

---

## 7. Pathway index

How to read it: **↑/↓** = direction of effect on the pathway · grade in brackets = best human evidence *for that pathway* · ⚠ = double-edged or adverse direction. Mechanism-level entries are [literature] unless marked [his framing].

### 7.1 Systemic inflammation ("the fire")
- **Human signal:** semaglutide / tirzepatide / retatrutide lower hsCRP (A/B as a marker, secondary to weight and metabolic change).
- **Animal only:** BPC-157 ↓NF-κB/TNF/IL-6 [D]; KPV ↓NF-κB [D]; TB-500 / Ac-SDKP anti-inflammatory [D]; GHK-Cu [D]; MOTS-c → NRF2 [D]; Epitalon "senescence" [D]; nicotine via α7 / cholinergic anti-inflammatory pathway [D for disease claims; C for ulcerative colitis, inferior to standard care]; methylene blue ↓ROS → NF-κB [D].
- **Not anti-inflammatory:** Thymosin α1 is an immune **stimulant** (TLR2/9), not an anti-inflammatory ⚠ [B for hepatitis only].
- ⚠ LL-37 can **drive** autoimmune inflammation (psoriasis/lupus autoantigen). ⚠ NAD+ boosting can amplify senescent-cell SASP (preclinical).

### 7.2 Insulin resistance ("the fuel problem")
- **Improve:** tirzepatide (T2D prevention, HR 0.07) [A]; semaglutide [A]; retatrutide (phase 3 topline HbA1c ↓) [B→A]; oral NMN (one small clamp RCT) [C].
- **Animal only:** MOTS-c → AMPK [D]; 5-Amino-1MQ [D]; Cardarine [D]; SLU-PP-332 [D].
- ⚠ **The GH axis worsens insulin sensitivity:** tesamorelin (HbA1c ≥6.5% in 5% vs 1%) [A, adverse]; MK-677 (↑fasting glucose) [B, adverse]; CJC-1295 / Ipamorelin / IGF-1 LR3 (class) [inferred].
 - Stacking GH secretagogues "for metabolism" works against this pathway.
- ⚠ Nicotine reduces insulin sensitivity [literature].

### 7.3 Mitochondrial dysfunction / ATP ("the power outage")
- SS-31 (cardiolipin): **A-narrow** in Barth syndrome; **negative** in primary mitochondrial myopathy.
- NAD+ / precursors (cofactor supply): **B** biomarker, **C/D** outcomes.
- Methylene blue (alternative electron carrier: NADH → cytochrome c, ↑Complex IV activity in a dysfunctional chain; biphasic) [D for fatigue/"ATP" outcomes; ⚠ MAO-A inhibition].
- **Animal only:** MOTS-c (AMPK, NRF2) [D]; 5-Amino-1MQ (NAD+ salvage) [D]; SLU-PP-332 (ERR) [D]; GHK-Cu (Complex IV copper claim) [D / his framing]; ARA-290 [D]; SR9009 [D].
- Retatrutide (glucagon ↑energy expenditure) [B surrogate].

### 7.4 Gut barrier
- **Animal only:** BPC-157 (mucosal cytoprotection, tight junctions) [D]; KPV (PepT1 uptake, colitis) [D]; TB-500 [D].
- GLP-1 class affects motility, **not** barrier repair (and causes GI adverse events) [A for adverse events].
- No compound in this file has human gut-barrier data.

### 7.5 Angiogenesis / tissue repair ⚠ (pro-angiogenic = double-edged in cancer)
- BPC-157 (VEGFR2 → Akt-eNOS) [D ⚠].
- Tβ4 (actin, migration, Ac-SDKP) [B-/C topical; D TB-500 ⚠].
- GHK-Cu (collagen, MMP/TIMP) [C topical].
- LL-37 [C topical ⚠].
- Dihexa (HGF/c-Met) [D ⚠].
- PEG-MGF, IGF-1 LR3 [D ⚠].
- CJC / Ipamorelin / Tesamorelin via IGF-1 ⚠ [label: contraindicated in active malignancy].

### 7.6 HPA axis / circadian
- **Weak or animal:** DSIP [D; PCAC rejected]; Epitalon (melatonin, primate) [D]; Selank [C/D].
- **Neutral:** Ipamorelin (little ACTH/cortisol) [pharmacology]; Kisspeptin (no cortisol effect in an n=95 controlled study) [B].
- Retatrutide → sympathetic/anxiety signal **[his framing]** (no trial data). Unclear direction.

### 7.7 Sex hormones / GH axis
- **GH axis:** Tesamorelin (GHRH-R) [A, HIV]; CJC-1295 (GHRH-R) [B surrogate]; Ipamorelin, MK-677 (GHSR) [B/D]; AOD-9604 [negative]; exogenous HGH [A labelled].
- **Gonadal axis:** Kisspeptin-10 (KISS1R → GnRH) [B probe; ⚠ chronic use desensitises]; SARMs (androgen receptor) [⚠ HPG suppression, B surrogate].
- **Melanocortin:** PT-141 (MC4R) [A-narrow]; Melanotan II [D ⚠].

### 7.8 Neuroinflammation / neuro
- Semaglutide in early Alzheimer's: **no benefit** (EVOKE/EVOKE+) [A-negative]. Retatrutide brain claims are **[his framing]** only.
- Cerebrolysin: stroke mortality **no benefit**, possible ↑SAEs [A-negative / C function].
- Methylene blue: small fMRI cognition study [C/D]; derivative (LMTM) failed phase 3 in Alzheimer's [negative]; ⚠ MAO-A inhibition / serotonin syndrome.
- Nicotine: attention in MCI [C]; Parkinson's progression **no benefit** (NIC-PD) [negative]; ⚠ dependence.
- Semax, Selank [C/D]; Dihexa [D ⚠]; BPC-157, KPV, MOTS-c, 5-Amino-1MQ (rodent) [D]; Aniracetam [C/D].

### 7.9 Autophagy / mTOR
- MOTS-c (AMPK → ↓mTOR, mitophagy) [D].
- NAD+/sirtuins [C/D]. SS-31 (mitochondrial quality) [D].
- ⚠ The GH / IGF-1 axis **activates mTOR and suppresses autophagy** [literature]. Combining "autophagy" peptides with GH secretagogues sends opposing signals [inferred].
- (Rapamycin and metformin are covered in Part B.)

### 7.10 Endothelial function / cardiovascular
- **Strongest human evidence in this file:** semaglutide **MACE HR 0.80** (SELECT) [A]. Tirzepatide and retatrutide lower SBP [A/B].
- **Animal only:** BPC-157 (eNOS/NO) [D]; ARA-290 [C/D]; TB-500 (cardiac, mouse) [D].
- **Adverse cardiovascular direction:** retatrutide ↑heart rate (dose-dependent) [B]; CJC-1295 tachycardia/vasodilation (FDA); PT-141 transient ↑BP [A]; Tesofensine ↑HR/BP [B]; Cardarine (rodent cancer) [D]; nicotine ↑HR/BP [A, label].

---

## 8. Agent rules derived from this file (non-negotiable)

1. **Never** output a dose, route, frequency, cycle, timing, sequencing, reconstitution or source for any compound in this file, including his own attributed numbers and the label doses of approved drugs. Approved drugs: "your prescriber sets and adjusts this."
2. Always separate **what the molecule does** (mechanism) from **what it has been shown to do for people** (grade). Use split grades by indication.
3. Name the double-edged mechanisms every time (angiogenesis, telomerase/ALT, GH/IGF-1, immune stimulation, NAD+/SASP, receptor desensitisation, MAO-A inhibition, nicotine dependence).
4. Hard-coded flags:
 - **GLP-1 class:** MTC/MEN 2 contraindication; aspiration before anaesthesia; hypoglycaemia with insulin/sulfonylureas.
 - **Tesamorelin:** active malignancy, pregnancy, glucose; lab changes go to the prescriber.
 - **Kisspeptin:** paradoxical suppression of the axis.
 - **Thymosin α1:** autoimmunity and transplant.
 - **GHK-Cu:** Wilson disease and copper overload.
 - **Methylene blue:** serotonin syndrome with SSRIs/SNRIs/MAOIs and other serotonergic drugs (boxed warning); G6PD deficiency; pregnancy.
 - **Nicotine:** dependence; heart disease/arrhythmia; pregnancy and adolescents.
 - **Any unapproved vial:** identity and purity unknown (retatrutide liver-injury cluster).
5. If/then rules end only in **stop, retest, or see the physician**. Never "reduce", "increase" or "hold" a dose. For a drug a physician prescribed, the action is **contact the prescriber**. Never tell the user to stop it on their own.
6. Never say "fire your doctor", never suggest stopping prescribed medication, never promise reversal or cure, never present FDA Category removal or a PCAC vote as approval.

---

## Sources (web-verified 2026-10-03, in addition to corpus files)

- FDA Category 2 removals (Apr 2026): [Frier Levitt](https://www.frierlevitt.com/articles/fda-peptides-do-not-compound-list-update-2026/) · [JD Supra](https://www.jdsupra.com/legalnews/tiny-chains-big-changes-what-fda-s-9395353/) · [Goodwin](https://www.goodwinlaw.com/en/insights/blogs/2026/05/fda-signals-potentially-evolving-stance-toward-compounding-of-certain-peptides)
- PCAC vote Jul 2026: [AJMC](https://ajmc.com/view/fda-panel-backs-6-peptides-for-compounding) · [McDermott](https://www.mcdermottlaw.com/insights/bulk-list-bound-pcac-backs-majority-of-peptides-in-two-day-public-meeting/) · [American Med Spa Assoc.](https://www.americanmedspa.org/news/fda-advisory-committee-recommends-adding-six-of-seven-peptides-to-compounding-list/)
- Retatrutide phase 3: [HCPLive](https://www.hcplive.com/view/retatrutide-meets-phase-3-weight-loss-endpoints-in-2-obesity-trials) · [Pharmacy Times](https://www.pharmacytimes.com/view/lilly-prepares-for-retatrutide-fda-filing-following-additional-phase-3-data-in-diabetes-cvd) · [Lilly investor release](https://investor.lilly.com/node/54736)
- Retatrutide grey-market liver injury: Victoria (Australia) Department of Health alert, 2026 (at least 6 cases of acute liver injury).
- Elamipretide approval: [FDA Drug Trials Snapshot](https://fda.gov/drugs/drug-trials-snapshots/drug-trials-snapshots-forzinity) · [HealthDay](https://www.healthday.com/healthpro-news/cardiovascular-diseases/fda-grants-accelerated-approval-for-first-treatment-for-barth-syndrome)
- NMN status: [Venable](https://www.venable.com/insights/publications/2025/10/fda-declares-nicotinamide-mononucleotide-is) · [NPA](https://www.npanational.org/news/fda-reinstates-nmn-as-dietary-supplement-after-npa-lawsuit/)
- EVOKE/EVOKE+: [Alzheimer Europe](https://www.alzheimer-europe.org/news/results-evoke-and-evoke-trials-show-no-effect-oral-semaglutide-ad-progression)
- Methylene blue label and evidence: [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=4f6848e5-35ed-4046-b13c-3032b5ba3232); PMIDs as listed in the corpus `literature_evidence_sheet`.
- Israel GLP-1 status: [Jerusalem Post](https://stgmobile.jpost.com/health-and-wellness/article-796423) · [Pharmaline (MoH letter)](https://pharmaline.co.il/wp-content/uploads/2024/04/רישום-ושיווק-התכשיר-וויגובי-WEGOVY-לטיפול-בהשמנת-יתר-והפסקת-טיפול-בתכשיר-אוזמפיק-OZEMPIC-להתוויה-זו.pdf) · [ynetnews Mounjaro](https://www.ynetnews.com/topics/Mounjaro) · [Israel Hayom health basket](https://www.israelhayom.co.il/health/article/20922263) · [Maccabi eligibility](https://www.maccabi4u.co.il/eligibilites/64054/?id=1548)

**Corpus files used:**
- `/tmp/claude-0/-home-user-nanobanana-mcp/8b82b4a5-08c5-5b73-b9c8-9cf6f2e6e556/scratchpad/research/corpus_substances.json`
- `/tmp/claude-0/-home-user-nanobanana-mcp/8b82b4a5-08c5-5b73-b9c8-9cf6f2e6e556/scratchpad/research/corpus_evidence.json`
- `/tmp/claude-0/-home-user-nanobanana-mcp/8b82b4a5-08c5-5b73-b9c8-9cf6f2e6e556/scratchpad/research/corpus_raw_norm.txt` (quote verification; WADA 2026 list text)
- `/home/user/nanobanana-mcp/.claude/skills/bio-protocol-agent/reference/01-style-guide.md`