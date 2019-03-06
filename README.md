# tshcal
Triaxial Sensor Head (TSH) Calibration

Tap into Python to control a 3-axis ESP motion controlled rig through a sequence of trajectories.  Ultimately, a feedback loop to control rig position using low-pass filtered acceleration measurements from a triaxial sensor head will yield calibration coefficients for the TSH.

### Roadmap

- [x] 2/28/19 Eric and Ken discuss big picture.
- [ ] Eric doing preliminary work with sockets to read data streaming from TSH.
- [ ] Ken get skeleton going for configuration, logging and argument parsing.
- [ ] Ken improve low-pass filtering for large data count values and vastly improved plotting.
- [ ] If possible, then have it so that acceleration client can either/or save to db table and pass values to subscribers (pub/sub).
- [ ] Goal is to translate to Python from some of Daveware, C++ code, to handle TSH **commanding, housekeeping and acceleration data**.
- [ ] Use PyCharm's Settings | Editor | TODO to add keyword for William (placeholder that he can help us with).  Similar to TODO and FIXME, but one reserved for him.
