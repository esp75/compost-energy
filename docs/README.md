# Documentation

The docs follow the [Diátaxis](https://diataxis.fr/) framework: four kinds of page, each for a different need. Pick the one that matches what you are trying to do.

| If you want to… | Read | Kind |
|---|---|---|
| Learn the project by doing something with it | [Tutorials](tutorials/) | learning-oriented |
| Get a specific task done | [How-to guides](how-to/) | task-oriented |
| Look up a number, a spec or a module | [Reference](reference/) | information-oriented |
| Understand why the design is what it is | [Explanation](explanation/) | understanding-oriented |

## Start here

1. [Run the model](tutorials/run-the-model.md): install the Python package and reproduce the energy model, the simulated prototype run and the figures. About 15 minutes.
2. [Farm-scale unit](reference/farm-unit.md): the design the model sizes, with the numbers.
3. [From home units to farm scale](explanation/pivot.md): why the first design was dropped.

## Pages

**Tutorials**
- [Run the model](tutorials/run-the-model.md)

**How-to guides**
- [Add measured data](how-to/add-measured-data.md)
- [Change a design assumption](how-to/change-a-design-assumption.md)

**Reference**
- [Farm-scale unit](reference/farm-unit.md): tunnels, heat recovery, controls, operating modes
- [System design](reference/system-design.md): chambers, process conditions, heat path, prototypes
- [Composting process](reference/process.md): recipe, phases, moisture and spray water per batch
- [Heat exchanger](reference/heat-exchanger.md): the 2024 calculation and its corrected figures
- [Provisional patent (2024)](reference/patent/provisional-patent-2024-EN.md): English translation; the [French original](reference/patent/provisional-patent-2024-FR.pdf) is alongside it

**Explanation**
- [Energy model](explanation/energy-model.md): does compost heat pay, at three scales
- [From home units to farm scale](explanation/pivot.md)
- [Configuration study](explanation/configuration-study.md): why four tunnels
- [Timeline](explanation/timeline.md)

## Labels

Every number in these docs is one of three things, and says which:

- **MODEL**: calculated from the assumptions in `model/compost_energy/`.
- **SIMULATED**: produced by the physics simulation of a prototype. Nothing has been measured with it.
- **MEASURED**: from a real logger run in `data/measured/`, or from a third-party dataset in `data/reference/` (with citation).
