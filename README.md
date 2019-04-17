# tshcal

This is a Python package to help automate triaxial sensor head (**tsh**) **cal**ibration. 

## Getting Started

These instructions will get you started with a copy of the project on your local machine.  Development has been geared for the Linux operating system.  Unit tests are included where we thought it was appropriate.  You should add your own tests, especially for parts of the code that you write and which warrant it, or for code you are depending on to verify changes there do not adversely affect you.   See deployment for notes on how to deploy the project on a production system.

### Prerequisites

What things you need to install the software and how to install them

```
Give examples
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc

Tap into Python to control a 3-axis ESP motion controlled rig through a sequence of trajectories.  Ultimately, a feedback loop to control rig position using low-pass filtered acceleration measurements from a triaxial sensor head will yield calibration coefficients for the TSH.

### Roadmap

- [x] 2/28/19 Eric and Ken discuss big picture.
- [ ] Eric doing preliminary work with sockets to read data streaming from TSH.
- [ ] Ken get skeleton going for configuration, logging and argument parsing.
- [ ] Ken improve low-pass filtering for large data count values and vastly improved plotting.
- [ ] If possible, then have it so that acceleration client can either/or save to db table and pass values to subscribers (pub/sub).
- [ ] Goal is to translate to Python from some of Daveware, C++ code, to handle TSH **commanding, housekeeping and acceleration data**.
