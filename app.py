def update_bracket_progress(knockout_data):
    # Play-off tamamlandıysa Yarı Final eşleşmelerini güncelle
    if "Play-off (Ön Eleme)" in knockout_data:
        po1 = knockout_data["Play-off (Ön Eleme)"][0]
        po2 = knockout_data["Play-off (Ön Eleme)"][1]

        if po1["score_home"] is not None and po1["score_away"] is not None:
            winner_po1 = po1["home"] if po1["score_home"] > po1["score_away"] else po1["away"]
            knockout_data["Yarı Final"][0]["away"] = winner_po1

        if po2["score_home"] is not None and po2["score_away"] is not None:
            winner_po2 = po2["home"] if po2["score_home"] > po2["score_away"] else po2["away"]
            knockout_data["Yarı Final"][1]["away"] = winner_po2

    # Yarı Final tamamlandıysa Final ve 3.'lük maçını güncelle
    sf1 = knockout_data["Yarı Final"][0]
    sf2 = knockout_data["Yarı Final"][1]

    if sf1["score_home"] is not None and sf1["score_away"] is not None and \
       sf2["score_home"] is not None and sf2["score_away"] is not None:
        
        w_sf1 = sf1["home"] if sf1["score_home"] > sf1["score_away"] else sf1["away"]
        l_sf1 = sf1["away"] if sf1["score_home"] > sf1["score_away"] else sf1["home"]

        w_sf2 = sf2["home"] if sf2["score_home"] > sf2["score_away"] else sf2["away"]
        l_sf2 = sf2["away"] if sf2["score_home"] > sf2["score_away"] else sf2["home"]

        knockout_data["Final"][0]["home"] = w_sf1
        knockout_data["Final"][0]["away"] = w_sf2

        knockout_data["3.lük Maçı"][0]["home"] = l_sf1
        knockout_data["3.lük Maçı"][0]["away"] = l_sf2
