"""Regenerates js/heroes.js and supabase/seed_heroes.sql.
Usage: python3 scripts/build_heroes.py path/to/card.json   (card.json from github.com/the-fab-cube/flesh-and-blood-cards)

The hero list was verified on 16 Nov 2026 against LSS's official Card Vault (cardvault.fabtcg.com):
67 young heroes are Silver Age legal and 4 are benched. The community dataset was missing four of them,
so those are listed by hand in EXTRA below. CARD overrides pick the newest plain printing for the portrait."""
import json, re, sys
BENCHED = {"Briar": "Outbreak (Feb 5, 2027)", "Chane": "Set 22 (2027)", "Oldhim": "Outbreak (Feb 5, 2027)", "Oscilio": "Outbreak (Feb 5, 2027)"}
# name -> (fabtcg.com icon path under cdn.fabtcg.com/uploads/, region theme colour)
I = {
"Arakni": ("2025/07/icon_arakni_th-1.webp", "#511d46"), "Arakni, Solitary Confinement": ("2025/11/icon_arakni_sttc-1.webp", "#511d46"),
"Arakni, Web of Deceit": ("2025/07/icon_arakni_m.webp", "#511d46"), "Aurora": ("2025/07/icon_aurora.webp", "#ff99ff"),
"Aurora, Emissary of Lightning": ("2026/03/icon_aurora_lot-2.webp", "#6a8bd8"), "Azalea": ("2025/06/icon_azalea.webp", "#511d46"),
"Benji, the Piercing Wind": ("2025/08/icon_benji.webp", "#698fbc"), "Betsy": ("2025/07/icon_betsy.webp", "#cc6633"),
"Blaze, Firemind": ("2026/03/icon_blaze.webp", "#990000"), "Boltyn": ("2025/07/icon_boltyn.webp", "#ffff99"),
"Bravo": ("2025/08/icon_bravo_s.webp", "#c7e4a1"), "Bravo, Flattering Showman": ("2026/01/icon_bravo_fs.webp", "#c0664c"),
"Briar": ("2025/07/icon_briar.webp", "#00ff99"), "Chane": ("2025/07/icon_chane.webp", "#660099"),
"Cindra": ("2025/07/icon_cindra.webp", "#990000"), "Dash": ("2025/08/icon_dash_ie.webp", "#993333"),
"Dash, Database": ("2025/07/icon_dash_io.webp", "#993333"), "Data Doll MKII": ("2025/06/icon_datadoll.webp", "#993333"),
"Dorinthea": ("2025/06/icon_dorinthea.webp", "#ffff99"), "Dorinthea, Quicksilver Prodigy": ("2026/07/icon_dorinthea_qp.webp", "#ffff99"),
"Dr. Mortimer": ("2026/08/icon_drmortimer_botp.webp", "#511d46"), "Dromai": ("2025/07/icon_dromai.webp", "#990000"),
"Enigma": ("2025/07/icon_enigma.webp", "#0066ff"), "Fai": ("2025/07/icon_fai.webp", "#990000"), "Fang": ("2025/04/icon_fang.webp", "#990000"),
"Florian": ("2025/07/icon_florian.webp", "#00ff99"), "Gravy Bones": ("2025/05/icon_gravybones.webp", "#00cc99"),
"Hala": ("2026/03/icon_hala_pos.webp", "#ffff99"), "Ira, Crimson Haze": ("2025/08/icon_ira.webp", "#698fbc"),
"Iyslander": ("2025/07/icon_iyslander.webp", "#99ffff"), "Kano": ("2025/08/icon_kano.webp", "#990000"),
"Kassai": ("2025/07/icon_kassai_gs.webp", "#cc6633"), "Kassai, Cintari Sellsword": ("2025/08/icon_kassai_cs.webp", "#990000"),
"Katsu": ("2025/07/icon_katsu.webp", "#698fbc"), "Kavdaen, Trader of Skins": ("2025/08/icon_kavdaen.webp", "#511d46"),
"Kayo": ("2025/07/icon_kayo_ad.webp", "#cc6633"), "Kayo, Berserker Runt": ("2025/08/icon_kayo_br_resized.png", "#006600"),
"Kayo, Strong-arm": ("2025/08/icon_kayo_uc-2.webp", "#c0664c"), "Killjoy, the Crooked Blade": ("2026/10/icon_killjoy_tcb.webp", "#cc6633"),
"Levia": ("2026/07/icon_levia_bod.webp", "#660099"), "Lexi": ("2025/07/icon_lexi.webp", "#ff99ff"),
"Lyath Goldmane": ("2025/08/icon_lyath-2.webp", "#c0664c"), "Marlynn": ("2025/07/icon_marlynn.webp", "#33cccc"),
"Maxx Nitro": ("2025/07/icon_maxxnitro.webp", "#993333"), "Nuu": ("2025/07/icon_nuu.webp", "#0066ff"),
"Oldhim": ("2025/06/icon_oldhim-1.webp", "#99ffff"), "Olympia": ("2025/07/icon_olympia.webp", "#cc6633"),
"Oscilio": ("2025/07/icon_oscillio.webp", "#ff99ff"), "Oscilio, Scion of the Third Age": ("2026/03/icon_oscilio_fc-1.webp", "#6a8bd8"),
"Pleiades": ("2025/08/icon_pleiades-1.webp", "#c0664c"), "Prism": ("2025/08/icon_prism_soa.webp", "#ffff99"),
"Puffin": ("2025/07/icon_puffin.webp", "#33cccc"), "Rhinar": ("2025/07/icon_rhinar_rr-1.webp", "#006600"),
"Riptide": ("2025/07/icon_riptide.webp", "#511d46"), "Scurv, Stowaway": ("2025/07/icon_scurv.webp", "#33cccc"),
"Teklovossen": ("2025/07/icon_teklovossen.webp", "#993333"), "Terra": ("2025/07/icon_terra.webp", "#00ff99"),
"Tuffnut": ("2025/08/icon_tuffnut-1.webp", "#c0664c"), "Uzuri": ("2025/07/icon_uzuri.webp", "#511d46"),
"Valda Brightaxe": ("2025/07/icon_valda.webp", "#c7e4a1"), "Verdance": ("2025/04/icon_verdance.webp", "#00ff99"),
"Victor Goldmane": ("2025/07/icon_victor.webp", "#ffff99"), "Viserai": ("2025/08/icon_viserai.webp", "#660099"),
"Vynnset": ("2025/07/icon_vynnset.webp", "#660099"), "Zane, Broadly Beloved": ("2026/10/icon_zane_bb.webp", "#cc6633"),
"Zen": ("2025/07/icon_zen.webp", "#0066ff"),
"Baalghor, Omen of the End": ("2026/05/icon_baalghor_oote.webp", "#660099"), "Malice": ("2026/07/icon_malice_dotd.webp", "#660099"),
"Prism, Advent of Thrones": ("2025/07/icon_prism_aos.webp", "#ffff99"), "Viserai, Between Worlds": ("2026/07/icon_viserai_tf.webp", "#a368b7"), "Zyggy": ("2026/03/icon_zyggy-1.webp", "#6a8bd8"),
}

EXTRA = [  # name, class, life, intellect, card print id
    ("Baalghor, Omen of the End", "Shadow Demon", 33, 3, "IAR159-RF"),
    ("Malice", "Shadow Necromancer", 20, 4, "IAR054"),
    ("Prism, Advent of Thrones", "Light Illusionist", 16, 4, "SAT001"),
    ("Viserai, Between Worlds", "Shadow Runeblade", 20, 4, "IAR107"),
]
CARD = {"Levia": "IAR002", "Bravo, Flattering Showman": "SMP002-RF"}
S3 = "https://legendstory-production-s3-public.s3.amazonaws.com/media/cards/normal/"
# fabtcg.com hero-selector cut-out art, keyed by icon file (path under cdn.fabtcg.com/uploads/, without "-scaled.ext")
CUT = dict(l.split(">") for l in """
icon_arakni_m.webp>2025/08/CHAOS-ASN-HERO-Arakni-Marionette-BLUE-IsuardiTherianto.webp
icon_arakni_th-1.webp>2025/08/ASSASSIN-HERO-Arakni-Huntsman-IsuardiTherianto.webp
icon_arakni_sttc-1.webp>2025/08/ASSASSIN-HERO-Arakni-Huntsman-IsuardiTherianto.webp
icon_aurora.webp>2025/08/ELE-RUNEBLADE-HERO-Aurora-Shooting-Star-AsurMisoa.webp
icon_aurora_lot-2.webp>2026/03/LIGHTNING-RUNEBLADE-HERO-Aurora-Legacy-of-Tempest-AsurMisoa-1.webp
icon_azalea.webp>2025/08/RANGER-BTA_T-Azalea-Maxim-Kostin.webp
icon_baalghor_oote.webp>2026/05/Baalghor_Omen-of-the-End-hero-selector.webp
icon_benji.webp>2025/08/CRU-NINJA-HERO-Benji-the-Piercing-Wind-Sam-Yang-1.webp
icon_betsy.webp>2025/08/GUARDIAN-HERO-Betsy-Odds-on-Favorite-SimonDominic.webp
icon_blaze.webp>2026/03/DRG-DRA-Blaze-Firemind-IsuardiTherianto.webp
icon_bravo_s.webp>2025/08/GUARDIAN-ALP_T-Bravo-Alexander-Mokhov-1.webp
icon_bravo_fs.webp>2026/02/GUARDIAN-HERO-Bravo-Flattering-Showman-WisnuTan-1.webp
icon_briar.webp>2025/08/TOA-ELE-RUNEBLADE-HERO-Briar-Warden-of-Thorns-Othon-Nikolaidis.webp
icon_chane.webp>2025/08/MON-SHADOW-RUNEBLADE-HERO-Chane-Black-Souled-Federico-Musetti.webp
icon_cindra.webp>2025/08/ROYAL-DRA-NINJA-HERO-Cindi-Dracai-of-Retribution-LiviaPrima.webp
icon_dash_ie.webp>2025/08/MECH-BTA_T-Dash-Inventor-Extraordinaire-Sam-Yang-1.webp
icon_dash_io.webp>2025/08/MECH-HERO-Dash-Motherboard-SamYang.webp
icon_datadoll.webp>2025/08/CRU-MECH-HERO-Data-Doll-MK-I-Tulinov-Roman.webp
icon_dorinthea_qp.webp>2026/07/RVD-WARRIOR-HERO-Dorinthea-Quicksilver-Prodigy.webp
icon_dorinthea.webp>2025/08/WARRIOR-ALP_T-Dorinthea-Ironsong-Lius-Lasahido.webp
icon_drmortimer_botp.webp>2026/08/ASN-HERO-Dr-Mortimer-Blight-of-the-Pits-OthonNikolaidis-1.webp
icon_dromai.webp>2025/08/DRG-DRA-ILLUS-HERO-Dromai-Adult-Kate-Fox-2.webp
icon_enigma.webp>2025/08/MST-ILLUS-HERO-Enigma-Mythwarden-AsurMisoa.webp
icon_fai.webp>2025/08/DRG-DRA-NINJA-Fai-Adult-Sam-Yang.webp
icon_fang.webp>2025/08/ROYAL-DRA-WARRIOR-HERO-Fang-Dracai-of-Blades-BillyChristian.webp
icon_florian.webp>2025/08/ELE-RUNEBLADE-HERO-Florian-Rotwood-Harbinger-Radial.webp
icon_gravybones.webp>2025/08/PIRATE-NECRO-HERO-Gravy-Bones-Shipwrecked-Looter-NathanielHimawan.webp
icon_hala_pos.webp>2026/03/WARRIOR-HERO-Hala-Goldenhelm-Paragon-of-Sol-FedericoMusetti.webp
icon_ira.webp>2025/08/NINJA-HERO-Ira-Scarlet-Revenger-STUDIO-1.webp
icon_iyslander.webp>2025/08/DRG-ELE-WIZARD-HERO-Iyslander-Adult-Alexander-Mokhov.webp
icon_kano.webp>2025/08/WIZARD-BTA_T-Kano-Alexander-Mokhov-1.webp
icon_kassai_cs.webp>2025/08/CRU-WARRIOR-Kaasai-Cintari-Sellsword-Alexander-Mokhov-1.webp
icon_kassai_gs.webp>2025/08/WARRIOR-HERO-Kassai-of-the-Golden-Sands-AlexanderMokhov.webp
icon_katsu.webp>2025/08/NINJA-ALP_T-Katsu-Adolfo-Navarro.webp
icon_kavdaen.webp>2025/08/CRU-MERCHANT-Kavdaen-Trader-of-Skins-Nikolay-Moskvin-1.webp
icon_kayo_br_resized.png>2025/08/CRU-BRUTE-Kayo-Berserker-RuntRadial-Studio-1.webp
icon_kayo_ad.webp>2025/08/BRUTE-HERO-Kayo-Armed-and-Dangerous-RADIAL.webp
icon_kayo_uc-2.webp>2025/08/centered_0013_REVILED-BRUTE-HERO-Kayo-Underhanded-Cheat-JessadaSutthi.png
icon_killjoy_tcb.webp>2026/08/WARRIOR-THIEF-HERO-Killjoy-the-Crooked-Blade-HenriqueLindner.webp
icon_levia_bod.webp>2025/08/SHADOW-BRUTE-HERO-Levia-Beckoner-of-Darkness-WisnuTan.webp
icon_lexi.webp>2025/08/TOA-ELE-RANGER-HERO-Lexi-Live-Wire-Federico-Musetti.webp
icon_lyath-2.webp>2025/08/REVILED-GUARDIAN-HERO-Lyath-Goldmane-Short-Tempered-NathanielHimawan-1.webp
icon_malice_dotd.webp>2026/07/SHADOW-NECRO-HERO-Malice-Adult-JoaoGSantos.webp
icon_marlynn.webp>2025/08/PIRATE-RANGER-HERO-Marlynn-Treasure-Hunter-SamYang.webp
icon_maxxnitro.webp>2025/07/MECH-HERO-Maxx-Nitro-_The-Breaker_-JessadaSutthi.webp
icon_nuu.webp>2025/08/MST-ASN-HERO-Nuu-Alluring-Desire-JessadaSutthi.webp
icon_oldhim-1.webp>2025/08/TOA-ELE-GUARDIAN-HERO-Oldhim-Grandfather-of-Eternity-Alexander-Mokhov.webp
icon_olympia.webp>2025/08/WARRIOR-HERO-Olympia-Prized-Fighter-JosephQiu.webp
icon_oscilio_fc-1.webp>2026/03/LIGHTNING-WIZARD-HERO-Oscilio-Scion-of-the-Third-Age-NathanielHimawan-1.webp
icon_oscillio.webp>2025/08/ELE-WIZARD-HERO-Oscilio-Constella-Intelligence-FedericoMusetti.webp
icon_pleiades-1.webp>2025/08/REVERED-GUARDIAN-HERO-Pleiades-Superstar-LiviaPrima-1.webp
icon_prism_aos.webp>2025/08/LIGHT-ILLUS-HERO-Prism-Awakener-of-Sol-LiviaPrima.webp
icon_prism_soa.webp>2025/08/MON-LIGHT-ILLUS-HERO-Prism-Sculptor-of-Arc-Light-Livia-Prima-1.webp
icon_puffin.webp>2025/08/PIRATE-MECH-HERO-Puffin-Full-Steam-Ahead-ArifWijaya.webp
icon_rhinar_rr-1.webp>2025/07/BRUTE-HERO-Rhinar-Reckless-Rampage-Deathmatch-WisnuTan-28.webp
icon_riptide.webp>2025/07/UPDATED-RANGER-HERO-Riptide-JosephQiu.webp
icon_scurv.webp>2025/08/PIRATE-THIEF-Scurv-SamYang.webp
icon_boltyn.webp>2025/08/MON-LIGHT-WARRIOR-HERO-Ser-Boltyn-Breaker-of-Dawn-Nikolay-Moskvin.webp
icon_teklovossen.webp>2025/07/fix_MECH-HERO-Professor-Teklovossen-Esteemed-Magnate-SimonDominicBrewer.webp
icon_terra.webp>2025/08/ELE-GUARDIAN-HERO-Terra-FedericoMusetti.webp
icon_tuffnut-1.webp>2025/08/REVERED-BRUTE-HERO-Tuffnut-Bumbling-Hulkster-WisnuTan-1.webp
icon_uzuri.webp>2025/08/ASN-HERO-Uzuri-JessadaSutthi.webp
icon_valda.webp>2025/08/GUARDIAN-HERO-Valda-Brightaxe-Seismic-Impact-WisnuTan.webp
icon_verdance.webp>2025/08/ELE-WIZARD-HERO-Verdance-Heart-of-the-Grove-LiusLasahido.webp
icon_victor.webp>2025/08/GUARDIAN-HERO-Victor-Goldmane-High-and-Mighty-BillyChristian.webp
icon_viserai_tf.webp>2026/07/SHADOW-RUNEBLADE-HERO-Viserai-the-Forsaken-NathanielHimawan.webp
icon_viserai.webp>2025/08/RUNEBLADE-BTA_T-Malthus-Steve-Argyle-2.webp
icon_vynnset.webp>2025/08/SHADOW-RUNEBLADE-HERO-Vynnset-Disciple-of-Pain-FedericoMusetti.webp
icon_zane_bb.webp>2026/08/REVERED-WARRIOR-HERO-Zane-Broadly-Beloved-SebastianGiacobino.webp
icon_zen.webp>2025/08/MST-NINJA-HERO-Zen-Tamer-of-Purpose-LiusLasahido.webp
icon_zyggy-1.webp>2026/03/LIGHTNING-ILLUS-HERO-Zyggy-Starlight-JessadaSutthi.webp
""".split())
cards = json.load(open(sys.argv[1]))
rows = []
for c in cards:
    if ({"Hero", "Young"} <= set(c["types"])) and c["silver_age_legal"]:
        imgs = [p["image_url"] for p in c["printings"] if p.get("image_url")]
        # Prefer a plain printing over foil / marvel scans: sort so the best one ends up last.
        def rank(u):
            f = u.rsplit("/", 1)[-1]
            return (0 if "MV" in f else 1 if "-CF" in f else 2 if "-RF" in f else 3)
        imgs.sort(key=rank)
        pid = imgs[-1].rsplit("/", 1)[-1].rsplit(".", 1)[0]
        rows.append((c["name"], " ".join(t for t in c["types"] if t not in ("Hero", "Young")), int(c["health"]), int(c["intelligence"]), pid))
have = {r[0] for r in rows}
rows += [e for e in EXTRA if e[0] not in have]
out = []
for name, cls, life, intel, pid in sorted(rows):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    icon, colour = I[name]
    cut, ext = CUT[icon.rsplit("/", 1)[-1]].rsplit(".", 1)
    out.append({"id": slug, "name": name, "cls": cls, "life": life, "int": intel,
                "art": S3 + CARD.get(name, pid) + ".webp",                     # young hero card, cropped to a circle
                "icon": "https://cdn.fabtcg.com/uploads/" + icon,              # fallback portrait
                "cutout": f"https://cdn.fabtcg.com/uploads/{cut}-1024x512.{ext}",
                "cutoutFull": f"https://cdn.fabtcg.com/uploads/{cut}" + ("" if "hero-selector" in cut else "-scaled") + f".{ext}",
                "colour": colour, "benched": BENCHED.get(name)})
open("js/heroes.js", "w").write("// Generated by scripts/build_heroes.py. Silver Age young heroes as of Mastery Pack Assassin (Nov 13, 2026).\nwindow.HEROES = " + json.dumps(out, indent=1, ensure_ascii=False) + ";\n")
rows = ",\n".join("  ('%s', '%s', %s)" % (h["id"], h["name"].replace("'", "''"), "false" if h["benched"] else "true") for h in out)
open("supabase/seed_heroes.sql", "w").write("-- Generated by scripts/build_heroes.py\ninsert into public.heroes (id, name, pickable) values\n" + rows + "\non conflict (id) do update set name = excluded.name, pickable = excluded.pickable;\n")
print(len(out), "heroes,", sum(1 for h in out if not h["benched"]), "pickable")
