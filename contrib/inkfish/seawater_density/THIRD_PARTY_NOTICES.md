# Third-party notices

Inkfish LLC. holds the copyright in its original code and documentation,
provided under the [MIT license](LICENSE). The notices below apply to
material adapted from third-party sources.

## Allen et al. (2025)

Allen, J. T., Keen, P. W., Nicholson, J., Quartley, M., Slade, I., and
Quartley, C. (2025). **TEOS10 compliant salinity and density equations for
sound speed instruments.** *Limnology and Oceanography: Methods*, **23**(11),
834–849. https://doi.org/10.1002/lom3.10715

Copyright © 2025 The Author(s).

Publisher: Wiley Periodicals LLC, on behalf of the Association for the
Sciences of Limnology and Oceanography.

The article is licensed under the **Creative Commons Attribution 4.0
International license (CC BY 4.0)**:

- Article: https://aslopubs.onlinelibrary.wiley.com/doi/full/10.1002/lom3.10715
- License: https://creativecommons.org/licenses/by/4.0/
- Legal terms, including the disclaimer of warranties and limitation of
  liability: https://creativecommons.org/licenses/by/4.0/legalcode.en
- Publisher-deposited license metadata:
  https://api.crossref.org/works/10.1002/lom3.10715

Material used: the density polynomial and the **Table 6, ρ (density) column**
coefficients in `logger/utils/seawater_density.py` and the reference formula
in `tests/test_water_density_transform.py`.

Adaptation: the equation is reduced to **sea pressure P = 0 dbar**, terms
containing pressure are omitted, and the remaining terms are implemented
in Python. The retained numerical coefficients are unchanged. The
OpenRVDAS integration, tests, examples, and TEOS-10 comparison tool were
added for this contribution. The integration includes adapted OpenRVDAS
code identified below. This implementation does not reproduce the full
pressure-dependent model. No author or publisher
endorsement is implied.

The article material retains its CC BY 4.0 license. Preserve this
attribution, source and license links, and change description when
redistributing the reused material or adaptations.

## OpenRVDAS

Portions of `logger/transforms/water_density_transform.py` are adapted from
OpenRVDAS's `logger/transforms/true_winds_transform.py`, including input-value
caching, update triggers, stale-value handling, and metadata emission.

The following copyright and MIT license apply to those adapted portions.
The notice is reproduced from the repository's [LICENSE](../../../LICENSE).
Inkfish's original additions and modifications are covered by this
contribution's [LICENSE](LICENSE).

```text
MIT License

Copyright (c) 2017 David Pablo Cohn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
