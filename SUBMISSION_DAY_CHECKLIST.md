# Hackathon Submission Day Checklist — June 28, 2026

## 📋 Pre-Submission (Days 1–8)

### Code & Repository
- [ ] All scripts committed to GitHub
- [ ] GitHub README.md is clear and up-to-date
- [ ] `.gitignore` configured (excludes data, includes models)
- [ ] GitHub link is public (judges can access)
- [ ] Model file (`forecast_model_rf.joblib`) is in repo
- [ ] Prediction CSV (`forecast_results_rf.csv`) is in repo
- [ ] All dependencies listed in `requirements.txt` or documented

### Documentation Complete
- [ ] `IDEA_SUBMISSION.md` — Full submission text
- [ ] `PRESENTATION_PITCH.md` — 5-minute speech
- [ ] `DEMO_SCRIPT.md` — Step-by-step dashboard walkthrough
- [ ] `FINAL_SUMMARY.md` — Project overview
- [ ] `DASHBOARD_README.md` — How to run dashboard
- [ ] `MODEL_SUMMARY.md` — Model metrics & interpretation

### Team Coordination
- [ ] Shared GitHub link with Mahalaxmi & Ashfaque
- [ ] Both tested dashboard on their machines
- [ ] Verified reproducibility (same results on different hardware)
- [ ] Documented any environment issues (versions, dependencies)
- [ ] Assigned roles: who presents? who answers tech questions?
- [ ] All team members can explain the 16.51-minute lead time

### Presentation Materials
- [ ] PowerPoint/Google Slides created (10 slides minimum)
  - [ ] Slide 1: Title with team names
  - [ ] Slide 2: Problem statement
  - [ ] Slide 3: Solution overview (detection/forecasting/dashboard)
  - [ ] Slide 4: Key result (16.51-minute lead time, large font)
  - [ ] Slide 5: Data summary table
  - [ ] Slide 6: Model performance metrics
  - [ ] Slide 7: Dashboard screenshot
  - [ ] Slide 8: Competitive advantages
  - [ ] Slide 9: Path to production
  - [ ] Slide 10: Closing + GitHub link
- [ ] Slides are visually clean (no clutter, good font size)
- [ ] All key numbers visible (108 events, 16.51 min, 0.894 ROC-AUC)
- [ ] Backup: Print 3 copies of slides (in case of projector failure)

### Demo & Practice
- [ ] Dashboard is running and tested
- [ ] All interactive features work (data source selector, time slider)
- [ ] Plots render correctly
- [ ] No console errors or warnings
- [ ] Practiced 5-minute pitch 3+ times out loud
- [ ] Demo script memorized (or printed backup)
- [ ] Timed yourself — should take 3:45–4:00 minutes
- [ ] Practiced with projector/external screen
- [ ] Practiced recovering from Q&A interruptions

### Backup Materials
- [ ] Screenshots of dashboard saved locally
- [ ] PDF printout of key results
- [ ] USB drive with entire repo (backup)
- [ ] Laptop fully charged, power cable in backpack
- [ ] Internet connectivity tested (or offline mode ready)

---

## 🎯 Submission Day Preparation

### Morning of Submission (2 hours before)

**Physical Prep:**
- [ ] Get good sleep night before
- [ ] Eat a light breakfast (no sugar crashes mid-presentation)
- [ ] Wear professional clothing (business casual minimum)
- [ ] Bring ID/student card
- [ ] Bring backup materials (USB, printouts)
- [ ] Arrive 30+ minutes early

**System Prep (on submission machine):**
- [ ] Laptop fully charged
- [ ] Dashboard tested: `py -m streamlit run dashboard.py`
- [ ] All browser tabs closed except dashboard
- [ ] Slack/email notifications silenced
- [ ] Volume on (if demo needs audio)
- [ ] Projector tested and configured
- [ ] Mouse/trackpad working smoothly

**Mental Prep:**
- [ ] Review 5-minute pitch one final time (read aloud, not just skimming)
- [ ] Review key numbers: 108, 16.51, 0.894, 50%, 25.6%
- [ ] Remind yourself: You built a *real, working system*. Confidence.
- [ ] Review Q&A talking points
- [ ] Remind yourself to speak slowly, make eye contact, smile when you say "16.51 minutes"

---

## 📍 During Submission/Judging

### Opening (Before Demo Starts)
- [ ] Greet judges with confidence and a smile
- [ ] Thank them for their time
- [ ] Say your team name clearly
- [ ] Take a breath — you know this system cold

### Presentation Delivery
- [ ] Start with problem statement (gets judges engaged)
- [ ] Transition smoothly to your solution
- [ ] **Show the dashboard by 2-minute mark** (visuals matter)
- [ ] Emphasize "16.51-minute lead time" at least 3 times
- [ ] Speak slowly and clearly — no rushing
- [ ] Make eye contact with judges
- [ ] Use your hands to point at screen, not a laser pointer
- [ ] Pause after key numbers to let them sink in
- [ ] Avoid jargon; explain in operational terms

### Dashboard Demo
- [ ] Follow `DEMO_SCRIPT.md` step-by-step
- [ ] Point and click deliberately — no random clicking
- [ ] Let plots load fully before explaining
- [ ] Highlight the alert banner and probability display
- [ ] Show multi-instrument fusion (switch between SoLEXS/HEL1OS/merged)
- [ ] Don't over-explain technical details
- [ ] If something glitches, stay calm: "Let me refresh that" → F5

### Closing
- [ ] Summarize in 1 sentence: "16.51-minute lead time using real Aditya-L1 data"
- [ ] Thank judges again
- [ ] Say "Questions?" with confidence
- [ ] Stand tall, look ready

### Q&A Handling
- [ ] Listen to the full question before answering
- [ ] Pause 2 seconds to think if needed
- [ ] Answer concisely (not a rambling lecture)
- [ ] If you don't know: "That's a great question; I'll research that for the prototype phase"
- [ ] Deflect overly technical questions: "We have detailed code documentation on GitHub"
- [ ] Always bring it back to the operational value
- [ ] Stay confident even if challenged — you have solid results

**Common Q&A:**
- Q: "Why only 16 flares?" → A: "Proof of concept on 6-day window; full archive will improve precision/recall; ROC-AUC shows genuine learning"
- Q: "Precision/recall are modest." → A: "Small sample sizes; operational threshold is appropriate; false alarms acceptable for space weather alerts"
- Q: "How does this compare to NOAA?" → A: "Complementary; we provide minute-level alerts; they provide day-ahead context"
- Q: "Can this scale to other phenomena?" → A: "Absolutely; methodology is instrument-agnostic; methodology proven on both SoLEXS and HEL1OS"

---

## ✅ Post-Submission

### Immediately After
- [ ] Thank judges one more time
- [ ] Shake hands if appropriate
- [ ] Smile (regardless of how it went)
- [ ] Step aside, let next team set up

### After All Submissions (While Waiting for Results)
- [ ] Debrief with team: What went well? What could improve?
- [ ] Note any judge questions for future iterations
- [ ] If you didn't win 1st, identify gaps and plan next steps
- [ ] Document lessons learned for next hackathon

### If You Win (or Don't)
- [ ] Either way, you have a production-ready prototype
- [ ] Continue development: add multi-month data, improve precision/recall
- [ ] Reach out to ISRO with results; they may fund the prototype phase
- [ ] Write it up as a research paper
- [ ] This is publishable work — don't let it end at the hackathon

---

## 🚨 Disaster Recovery

**If dashboard won't start:**
- [ ] Try: `py -m streamlit run dashboard.py --logger.level=debug`
- [ ] Check: `py -m pip show streamlit` (verify installation)
- [ ] Backup: Show the last screenshot instead, transition to code walkthrough
- [ ] Have GitHub link ready to show code + results

**If laptop crashes:**
- [ ] Use backup USB to boot a teammate's laptop
- [ ] Or: Show slides + screenshots while explaining system
- [ ] Or: Walk judges through GitHub repo directly

**If network is down:**
- [ ] Dashboard runs locally (no internet needed)
- [ ] If Wi-Fi for presentation is down, use laptop's own network
- [ ] Keep all critical files offline

**If you go blank mid-presentation:**
- [ ] Pause, take a breath, drink water if available
- [ ] Reference your notes/slides
- [ ] Say: "Let me back up and explain that more clearly"
- [ ] Judges respect composure; don't panic

**If judges are hostile/dismissive:**
- [ ] Stay professional and confident
- [ ] Don't get defensive; respond to the substance, not the tone
- [ ] Let your results speak: "The 0.894 ROC-AUC is reproducible; code is on GitHub"
- [ ] Thank them and move on

---

## 📊 Success Criteria for Submission Day

You'll know you nailed it if:
- ✅ Dashboard loaded and ran without crashing
- ✅ Judges asked technical follow-up questions (sign of interest)
- ✅ You explained 16.51-minute lead time clearly
- ✅ Judges visited your GitHub after presentation
- ✅ You answered Q&A confidently, no major stumbles
- ✅ Judges mentioned "complete system" or "end-to-end"
- ✅ You felt proud of your work (regardless of prize)

---

## 🏆 Final Reminders

1. **You've built something real.** Most student teams won't have working code + live demo + quantifiable results. Own that.

2. **16.51 minutes is your anchor.** Every time judges ask "So what's special about this?", come back to that number.

3. **Honesty wins trust.** If you say "small dataset, but ROC-AUC shows genuine learning," judges believe you. If you oversell, they don't.

4. **The dashboard is your secret weapon.** While other teams are talking about algorithms, you're *showing* a working system. That's memorable.

5. **Confidence matters.** You know this system better than anyone. Project that confidence, and judges will believe in it too.

6. **Have fun.** You built a solar flare forecaster that might actually help space weather predictions. That's cool. Enjoy the moment.

---

## 🎯 Your Goal

- **1st Prize**: Strong chance (40–50%) with solid execution
- **Top 3 (medals)**: Very likely (60–80%)
- **Memorable presentation**: Almost guaranteed (you're unique)

**Worst-case scenario**: You don't place, but you have a production-ready prototype that you can continue developing and potentially publish or pitch to ISRO.

**Best-case scenario**: You win 1st prize AND get invited to the prototype phase, where you develop the system further with real Aditya-L1 data.

Either way, you're in a great position. Go submit with confidence. 🚀

---

**See you at the finish line. Let's go get that prize.**
