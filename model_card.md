# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**TuneScout 1.0**: a small recommender that scouts a song catalog for tracks that match a listener's vibe.

---

## 2. Goal and Intended Use  

**Goal / task.** TuneScout suggests the 5 songs from its catalog that best fit one listener's taste. It doesn't predict ratings or learn from listening history. It scores every song against what the user says they want and explains why each song made the list.

**Intended use.** TuneScout is a classroom project for learning how content-based recommenders work. It's meant for exploring questions like "what happens if energy counts more than genre?" and for seeing how scoring rules can create bias. It assumes the user can describe their taste with one favorite genre, one mood, a target energy level, a target brightness (valence) and whether they like acoustic sound.

**Non-intended use.** TuneScout shouldn't be used to make recommendations for real listeners or in a real music app. Its catalog is 18 made-up songs, its mood labels were assigned by hand, and it has never been checked against what real people actually enjoy. It also shouldn't be used to judge whether a genre or artist is "good": a low score only means a song didn't match one particular profile.

---

## 3. How the Model Works  

TuneScout works like a judge giving each song points for how well it fits what you asked for. The highest possible score is 5.

- **Energy (up to 2 points).** This is the most important rule. Songs get more points the closer their energy is to the level you want. A song that's *too* intense loses points just like one that's too calm, so "louder" isn't automatically "better".
- **Genre (1 point).** A song gets 1 point if it's your favorite genre.
- **Mood (1 point).** A song gets 1 point if its mood label matches yours, such as "happy" or "chill".
- **Brightness (up to 0.5 points).** Songs that sound about as cheerful or as dark as you want get a small bonus.
- **Acoustic sound (up to 0.5 points).** If you like acoustic music, more acoustic songs get a small bonus. If you don't, electronic and produced songs get it instead.

TuneScout adds up the points, sorts the songs from highest to lowest, and shows the top 5 with a list of reasons, like "genre match: pop (+1.0)".

**Changes from the starter logic.** The starter code had no scoring at all, so we built these rules from scratch. We also made the system forgiving of small input mistakes: "Pop" counts the same as "pop", "False" written as text is understood, and energy targets above 1 or below 0 are capped. Originally genre was worth 2 points and energy 1. Testing showed that genre was overpowering everything else, so we swapped them.

---

## 4. Data  

- **Size.** The catalog has 18 songs. The starter file had 10, and we added 8 more (ids 11–18) to cover genres and moods that were missing. All titles and artists are fictional.
- **Features.** Each song has a title, artist, genre and mood, plus five numbers: energy, valence (brightness), danceability and acousticness on a 0–1 scale, and tempo in beats per minute. TuneScout scores energy, valence and acousticness. Tempo and danceability aren't used, because in this data they mostly rise and fall with energy, so scoring them would count the same thing twice.
- **Genres and moods.** There are 15 genres and 14 moods. They're very unevenly spread: lofi has 3 songs and pop has 2, but the other 13 genres have just 1 song each. "Chill" has 3 songs, "happy" and "intense" have 2 each, and the other 11 moods have 1 each.
- **Limits.**
  - Each song has only one mood label, chosen by hand, even though real songs often fit several.
  - The numbers were made up to fit the labels, not measured from real audio.
  - The data says nothing about lyrics, language, era, popularity or culture.
  - There's no listening history, so the system can't learn what anyone actually likes.

---

## 5. Strengths  

- **Clear, consistent tastes get good results.** The happy-pop listener gets *Sunrise City* first (4.85 out of 5), and it matches on every rule.
- **Opposite users get opposite lists.** The upbeat pop fan and the calm, acoustic listener share no songs at all in their top 5, which is what you'd expect.
- **"Close" beats "more".** Because energy is scored by closeness, a listener who wants calm music gets calm songs instead of the loudest ones.
- **It explains itself.** Every recommendation lists the points it earned, so it's easy to see why a song like *Gym Hero* shows up, and to spot when a pick is just filler.
- **It handles messy input.** Capital letters, a "False" typed as text and out-of-range energy values all give sensible results instead of wrong scores or crashes.

---

## 6. Limitations and Bias 

The system gives much worse recommendations to users with less common tastes, because the catalog is uneven: of 18 songs, lofi has 3 and pop has 2, but the other 13 genres have only one song each. A lofi fan can get three genre matches, while a metal fan can get at most one, so the rest of their top 5 is filled by songs from other genres. In the "Missing keys" test (a pop-only profile), positions #3–#5 all scored 0.00 and appeared only because of their order in the CSV, not because they matched anything. In the "Contradictory metal" test, the only metal song (energy 0.97) was so far from the requested energy 0.1 that it fell to #8, leaving the user with no metal in their top 5 at all. Our weight shift (genre +2.0 → +1.0) made this worse for single-genre fans, so the real fix is a larger, more balanced catalog rather than more weight tuning.

---

## 7. Evaluation  

We evaluated the recommender by running `python -m src.main`, which scores all 18 songs for seven user profiles, and reading each top 5 along with its reasons.

**Profiles tested**

| Profile | Why we tested it | Top result (score) |
|---|---|---|
| Default (pop, happy, energy 0.80) | A normal, consistent user | Sunrise City (4.85) |
| Capitalized labels (`"Pop"`, `"Happy"`) | Case-sensitive matching | Sunrise City (4.85), same as default |
| String boolean (`likes_acoustic: "False"`) | Python treats `"False"` as true | Sunrise City (4.85), same as default |
| Energy out of range (1.5) | Targets outside 0.0–1.0 | Sunrise City (4.53), no negative points |
| Missing keys (genre only) | Incomplete profile | Sunrise City and Gym Hero (1.00 each), then three songs at 0.00 |
| High-energy lofi fan (lofi, chill, energy 0.95) | Genre and energy pulling in opposite directions | Midnight Coding (3.56) |
| Contradictory metal (metal, peaceful, energy 0.1) | Genre and mood pulling in opposite directions | Moonlit Sonata Redux (3.76) |

**What we looked for**

- Songs that match the user's genre and mood should rank first.
- A song *near* the user's energy target should beat one that is simply higher.
- Every reason should add up to the score shown, and no rule should give negative points.
- Small input mistakes, such as capital letters or a string instead of a boolean, should not change the results.

**What surprised us**

- The first version failed four of the seven profiles. Capitalized labels dropped Sunrise City from 4.87 to 1.87, `"False"` was read as "likes acoustic", energy 1.5 gave calm songs negative points, and the genre-only profile crashed the display. All four are now fixed.
- Genre was too powerful under the original weights (genre +2.0, energy 1.0×). The pop fan got *Gym Hero* (the wrong mood) above *Rooftop Lights* (the right mood), and the lofi fan who asked for energy 0.95 got only calm songs.
- Fixing that had a cost. After the weight shift, the metal fan's only metal song fell from #2 to #8.

**Comparisons and tests**

- **Weight experiments:** we compared the original weights, a weight shift (genre +1.0, energy 2.0×) and removing mood, on the same profiles. The weight shift was kept, and removing mood was rejected because it made every tested ranking worse. The full tables are in the README under "Experiments You Tried".
- **Automated tests:** `pytest` runs two unit tests. They check that a pop/happy user gets the pop/happy song first and that every recommendation comes with a non-empty explanation. Both pass.
- We did not use numeric accuracy metrics, because there is no real listening data to compare against. The evaluation is based on whether the rankings and reasons make sense for each profile.

### Comparing profiles

**Why does "Gym Hero" keep showing up for someone who just wants happy pop?**
Think of the recommender as a judge handing out points. Gym Hero misses only one thing the happy-pop listener asked for: it is labeled "intense" instead of "happy". Everything else lines up. It is pop (+1.0). Its energy is 0.93, close to the 0.80 they wanted (+1.74 out of 2). It still sounds fairly bright (+0.48), and it is an electronic, non-acoustic track like they prefer (+0.47). That adds up to 3.70 out of 5, and there are only two pop songs in the whole catalog, so Gym Hero is the "other pop song" almost by default. Under the original weights it came in at #2. After we made energy count more than genre, *Rooftop Lights* (happy, but "indie pop") overtook it, and Gym Hero dropped to #3 by just 0.04 points. It still shows up because it is nearly right and the catalog doesn't have many better options.

**Every pair of the seven profiles, compared**

| Profiles compared | What changed, and why it makes sense |
|---|---|
| Default vs. Capitalized labels | Exactly the same list and scores. Typing "Pop" instead of "pop" is the same request, so it should get the same answer. |
| Default vs. String boolean | Exactly the same. Writing "not acoustic" as the text `"False"` means the same thing, so nothing should change. |
| Default vs. Energy out of range | Same #1 (Sunrise City), but Gym Hero (energy 0.93) climbs from #3 to #2, and the metal track *Iron Tempest* (0.97) joins at #5. Asking for "as intense as possible" pulls the loudest songs up, which is what that user wants. |
| Default vs. Missing keys | The top score drops from 4.85 to 1.00 and *Rooftop Lights* disappears. The system only knows "pop", so it can't tell a happy song from an intense one, and it fills the rest of the list with leftovers. Less information means weaker picks. |
| Default vs. High-energy lofi fan | The top three are completely different: upbeat pop for one, calm lofi for the other, because they named different genres and moods. *Neon Pulse* (EDM, energy 0.95) appears in both lists because both users asked for high energy. |
| Default vs. Contradictory metal | No songs in common. The default user gets bright, electronic, upbeat songs. The metal profile asked for peaceful, very low-energy (0.1), acoustic music, so it gets quiet piano, folk and ambient tracks. Opposite requests give opposite lists. |
| Capitalized labels vs. String boolean | Identical to each other. Both test a typing mistake, and the system correctly ignores both mistakes. |
| Capitalized labels vs. Energy out of range | Both are "messy input" tests, but only the energy one changes the list. Capital letters don't change the meaning, while energy 1.5 really does mean "as high as possible". |
| Capitalized labels vs. Missing keys | The capitalized profile still scores 4.85 because the system understood "Pop" and "Happy". The missing-keys profile tops out at 1.00. A messy but complete profile beats a tidy but nearly empty one. |
| Capitalized labels vs. High-energy lofi fan | "Happy" pulls in bright songs like *Rooftop Lights*, while "chill" pulls in *Midnight Coding* and *Library Rain*. The mood word clearly steers the top of the list. |
| Capitalized labels vs. Contradictory metal | The capitalized profile wants energy 0.80 and gets songs around 0.76–0.95. The metal profile wants 0.1 and gets songs around 0.18–0.37. Energy is now the biggest factor, so the two lists sit at opposite ends of the energy scale. |
| String boolean vs. Energy out of range | Same pop/happy taste, so the top song is the same. Raising energy to the maximum swaps *Concrete Crown* (0.78) out for *Iron Tempest* (0.97). |
| String boolean vs. Missing keys | The string-boolean profile is complete, so its reasons list five things per song. The missing-keys profile's songs earn at most one reason ("genre match"), and three songs earn none. More preferences lead to better explanations as well as better picks. |
| String boolean vs. High-energy lofi fan | Both said "not acoustic", but lofi songs *are* fairly acoustic (0.71–0.86), so they earn almost no acoustic points (+0.07 to +0.15). They still win the top two spots for the lofi fan because they match the genre and mood. |
| String boolean vs. Contradictory metal | The acoustic setting flips. "Not acoustic" gives electronic tracks (acousticness 0.02–0.35), while "acoustic" gives a top 5 where every song is 0.86 or higher. The acoustic preference does its job. |
| Energy out of range vs. Missing keys | One profile asks for too much (energy 1.5) and one asks for too little (only a genre). The first still gets a sensible list, because 1.5 is treated as "maximum". The second gets filler, because there is nothing to judge the other songs on. |
| Energy out of range vs. High-energy lofi fan | Both want very high energy, and they share *Neon Pulse* and *Iron Tempest*. What differs is the top of each list: genre and mood bonuses lift pop songs for one user and lofi songs for the other. |
| Energy out of range vs. Contradictory metal | *Iron Tempest* is #5 for the max-energy pop fan, who never asked for metal, but #8 for the user who *did* ask for metal. That looks backwards, but it follows the rules: energy counts most, and the metal fan asked for very low energy. |
| Missing keys vs. High-energy lofi fan | *Midnight Coding* and *Library Rain* appear in both lists. For the missing-keys profile they score 0.00 and appear only because of their place in the file. For the lofi fan they score 3.56 and 3.32 because they truly match. Same songs, completely different reasons, which is why showing the reasons matters. |
| Missing keys vs. Contradictory metal | Both show that the catalog is thin. There are only two pop songs, so the pop-only user runs out of matches after #2. There is only one metal song, so the metal fan gets no metal at all once energy is taken into account. |
| High-energy lofi fan vs. Contradictory metal | Both users ask for things that conflict, and in both cases the side with more matching points wins. For the lofi fan, genre and mood (2.0 points together) beat energy, so lofi takes #1–#2. For the metal fan, mood, energy and acoustic preference all point the same way and outvote genre, so no metal appears. |

---

## 8. Future Work  

1. **A bigger, more balanced catalog, with partial credit for related labels.** Every genre should have several songs, so fans of rarer genres get real matches instead of filler. Related labels should also earn some points, for example "indie pop" counting partly as "pop" and "relaxed" partly as "chill", instead of getting nothing.
2. **More variety in the top 5.** Add a rule that limits how many songs can come from one artist. If the user's genre exists in the catalog, at least one song of that genre should appear, so the metal fan always gets some metal.
3. **Richer taste profiles.** Let users choose more than one genre or mood, and let songs carry several mood labels. Also support listeners who like *both* very calm and very intense music, which the current single energy target can't represent.

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
