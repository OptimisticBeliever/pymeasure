#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2023 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

from time import sleep
from unittest.mock import ANY

import numpy as np
import pytest
from pyvisa.errors import VisaIOError

from pymeasure.instruments.lecroy.LecroyWR606Zi import LecroyWR606Zi


class TestLecroyWR606Zi:
    """
    Unit tests for LecroyWR606Zi class.

    This test suite, needs the following setup to work properly:
        - A LecroyWR606Zi device should be connected to the computer;
        - The device's address must be set in the RESOURCE constant;
        - A probe on Channel 1 must be connected to the Demo output of the oscilloscope.
    """

    #########################
    # PARAMETRIZATION CASES #
    #########################

    BOOLEANS = [False, True]
    CHANNEL_COUPLINGS = ["ac", "dc", "ground"]
    SAMPLING_MODES = ["RealTime", "Sequence"]
    TRIGGER_LEVELS = [0.125, 0.150, 0.175]
    TRIGGER_SLOPES = ["negative", "positive"]
    TRIGGER_TYPES = ["edge", "pulse", "interval", "runt", "slewrate", "glitch", "pattern",
                     "dropout", "tv"]
    ACQUISITION_AVERAGE = [4, 16, 32, 64, 128, 256]
    WAVEFORM_POINTS = [100, 1000, 10000]
    WAVEFORM_SOURCES = ["C1", "C2", "C3", "C4"]
    CHANNELS = [1, 2, 3, 4]
    BANDWIDTH_LIMITS = ["1GHz", "20MHz", "200MHz"]
    MEAS_SLOTS = {1: "PKPK", 2: "WID", 3: "DUTY", 4: "FREQ"}
    EXPECTED_MEAS_VALUES = {'PKPK': 1, 'WID': 500.0000E-6, 'DUTY': 50,
                            'FREQ': 1.0000E3}
    PARAM_ENGINE = ["Amplitude", "Area", "Base", "Cycles", "Delay", "DeltaDelay",
                    "DeltaPeriodAtLevel", "DeltaTimeAtLevel", "DeltaTriggerTime",
                    "DeltaWidthAtLevel", "Duration", "DutyAtLevel", "DutyCycle",
                    "Fall", "Fall8020", "FallAtLevel", "FirstPoint", "Frequency",
                    "FrequencyAtLevel", "FullWidthAtHalfMaximum", "FullWidthAtXX",
                    "HalfPeriod", "HistogramAmplitude", "HistogramBase", "HistogramMaximum",
                    "HistogramMean", "HistogramMedian", "HistogramMinimum",
                    "HistogramRms", "HistogramSdev", "HistogramTop", "HoldTime",
                    "LastPoint", "LevelAtX", "MATLABParameter", "Maximum",
                    "MaximumPopulation", "Mean", "Median", "Minimum", "Mode", "NCycleJitter",
                    "npoints", "Null", "OvershootNegative", "OvershootPositive", "Peaks",
                    "PeakToPeak", "Percentile", "Period", "PeriodAtLevel", "Phase",
                    "PopulationAtX", "Range", "Rise", "Rise2080", "RiseAtLevel", "RootMeanSquare",
                    "Setup", "Skew", "Slew", "StandardDeviation", "TIE", "TimeAtLevel", "Top",
                    "TotalPopulation", "Width", "WidthAtLevel", "WidthNegative", "XAtMaximum",
                    "XAtMinimum", "XAtPeak"]

    FULL_PARAM_ENGINE = ["Amplitude", "Area", "Base", "Cycles", "Delay", "DeltaDelay",
                      "DeltaPeriodAtLevel", "DeltaTimeAtLevel", "DeltaTriggerTime",
                      "DeltaWidthAtLevel", "DOV", "Duration", "DutyAtLevel", "DutyCycle",
                      "DutyCycleDistortion", "EdgeAtLevel", "EMClvlPulse", "EMCt2Val",
                      "EOvshN", "EOvshP", "ExcelParam", "ExtinctionRatio", "EyeAmplitude",
                      "EyeAvgPower", "EyeBER", "EyeCrossing", "EyeHeight", "EyeOneLevel",
                      "EyeQFactor", "EyeWidth", "EyeZeroLevel", "Fall", "Fall8020",
                      "FallAtLevel", "FastMultiWPort", "FirstPoint", "Frequency",
                      "FrequencyAtLevel", "FullWidthAtHalfMaximum", "FullWidthAtXX",
                      "GapWidth", "GBM1FGDroop", "GBM1HJDroop", "HalfPeriod",
                      "HistogramAmplitude", "HistogramBase", "HistogramMaximum",
                      "HistogramMean", "HistogramMedian", "HistogramMid", "HistogramMinimum",
                      "HistogramRms", "HistogramSdev", "HistogramTop", "HoldTime",
                      "HParamScript", "I2StoValue", "LastPoint", "LevelAtX", "LocalBase",
                      "LocalBaselineSeparation", "LocalMaximum", "LocalMinimum", "LocalNumber",
                      "LocalPeakToPeak", "LocalTimeAtMaximum", "LocalTimeAtMinimum",
                      "LocalTimeBetweenEvent", "LocalTimeBetweenPeaks", "LocalTimeBetweenTroug",
                      "LocalTimeOverThreshold", "LocalTimePeakToTrough", "LocalTimeTroughToPeak",
                      "LocalTimeUnderThreshol", "MathcadParam", "MATLABParameter", "Maximum",
                      "MaximumPopulation", "Mean", "Median", "Minimum", "Mode", "NarrowBandPhase",
                      "NarrowBandPower", "NCycleJitter", "NonLinearTransitionShift", "npoints",
                      "Null", "NumberOfModes", "OvershootNegative", "OvershootPositive",
                      "Overwrite", "ParamScript", "PEAKMAG", "Peaks", "PeakToPeak", "Percentile",
                      "Period", "PeriodAtLevel", "Phase", "PopulationAtX", "PowerFactor",
                      "Protocol2Analog", "Protocol2Protocol", "Protocol2Value", "ProtocolBitrate",
                      "ProtocolLoad", "ProtocolNumMessages", "PW50", "PW50Negative",
                      "PW50Positive", "Range", "RealPower", "Resolution", "Rise", "Rise2080",
                      "RiseAtLevel", "RootMeanSquare", "SAS", "Setup", "Skew", "Slew",
                      "StandardDeviation", "TAA", "TAANegative", "TAAPositive", "TIE",
                      "TimeAtCAN", "TimeAtLevel", "TimeAtProtocol", "Top", "TotalPopulation",
                      "tUpS", "Width", "WidthAtLevel", "WidthNegative", "XAtMaximum",
                      "XAtMinimum", "XAtPeak"]

    ############
    # FIXTURES #
    ############

    @pytest.fixture(scope="module")
    def instrument(self, connected_device_address):
        return LecroyWR606Zi(connected_device_address)

    @pytest.fixture
    def resetted_instrument(self, instrument):
        instrument.reset()
        sleep(2)
        return instrument

    @pytest.fixture
    def autoscaled_instrument(self, instrument):
        instrument.reset()
        sleep(5)
        instrument.autoscale()
        sleep(5)
        return instrument

    #########
    # TESTS #
    #########

    # noinspection PyTypeChecker
    def test_instrument_connection(self):
        bad_resource = "USB0::0x05FF::0x1023::3212N62548::INSTR"
        # The pure python VISA library (pyvisa-py) raises a ValueError while the
        # PyVISA library raises a VisaIOError.
        with pytest.raises((ValueError, VisaIOError)):
            LecroyWR606Zi(bad_resource)

    # Channel
    def test_ch_current_configuration(self, resetted_instrument):
        expected = {
            "channel": 1,
            "attenuation": 10.0,
            "bandwidth_limit": "1GHz",
            "coupling": "dc",
            "offset": 0.0,
            "display": True,
            "volts_div": 0.5,
            "inverted": False,
            "trigger_edge_coupling": "dc",
            "trigger_level": 0.0,
            "trigger_edge_slope": "positive",
        }
        actual = resetted_instrument.ch(1).current_configuration
        assert actual == expected

    @pytest.mark.parametrize("ch_number", CHANNELS)
    @pytest.mark.parametrize("case", BANDWIDTH_LIMITS)
    def test_ch_bwlimit(self, instrument, ch_number, case):
        instrument.ch(ch_number).bwlimit = case
        assert instrument.ch(ch_number).bwlimit == case

    @pytest.mark.parametrize("ch_number", CHANNELS)
    @pytest.mark.parametrize("case", CHANNEL_COUPLINGS)
    def test_ch_coupling(self, instrument, ch_number, case):
        instrument.ch(ch_number).coupling = case
        assert instrument.ch(ch_number).coupling == case

    @pytest.mark.parametrize("ch_number", CHANNELS)
    @pytest.mark.parametrize("case", BOOLEANS)
    def test_ch_display(self, instrument, ch_number, case):
        instrument.ch(ch_number).display = case
        assert instrument.ch(ch_number).display == case

    @pytest.mark.parametrize("ch_number", CHANNELS)
    @pytest.mark.parametrize("case", BOOLEANS)
    def test_ch_invert(self, instrument, ch_number, case):
        instrument.ch(ch_number).invert = case
        assert instrument.ch(ch_number).invert == case

    @pytest.mark.parametrize("ch_number", CHANNELS)
    def test_ch_offset(self, instrument, ch_number):
        instrument.ch(ch_number).offset = -0.1
        assert instrument.ch(ch_number).offset == -0.1

    @pytest.mark.skip(reason="connect third-party probes on channels")
    @pytest.mark.parametrize("ch_number", CHANNELS)
    def test_ch_probe_attenuation(self, instrument, ch_number):
        instrument.ch(ch_number).probe_attenuation = 10
        assert instrument.ch(ch_number).probe_attenuation == 10

    @pytest.mark.parametrize("ch_number", CHANNELS)
    def test_ch_scale(self, instrument, ch_number):
        instrument.ch(ch_number).scale = 1
        assert instrument.ch(ch_number).scale == 1

    @pytest.mark.parametrize("trig_level", TRIGGER_LEVELS)
    @pytest.mark.parametrize("ch_number", CHANNELS)
    def test_ch_trigger_level(self, trig_level, ch_number, resetted_instrument):
        resetted_instrument.ch(ch_number).trigger_level = trig_level
        assert resetted_instrument.ch(ch_number).trigger_level == trig_level

    def test_ch_trigger_slope(self, instrument):
        with pytest.raises(ValueError):
            instrument.ch_1.trigger_slope = "abcd"
        instrument.trigger_select = ("edge", "c2", "off")
        for case in self.TRIGGER_SLOPES:
            # Bug trigger slope always return positive
            instrument.ch_1.trigger_slope = case
            # assert instrument.ch_1.trigger_slope == case

    @pytest.mark.parametrize("case", TRIGGER_TYPES)
    def test_trigger_type(self, case, instrument):
        instrument.trigger_type = case
        assert instrument.trigger_type == case

    # Timebase
    def test_timebase(self, resetted_instrument):
        expected = {
            "timebase_scale": 5e-8,
            "timebase_offset": 0.0,
        }
        actual = resetted_instrument.timebase
        for key, val in actual.items():
            assert pytest.approx(val, 0.1) == expected[key]

    def test_timebase_scale(self, resetted_instrument):
        resetted_instrument.timebase_scale = 1e-3
        assert resetted_instrument.timebase_scale == 1e-3

    def test_timebase_offset(self, resetted_instrument):
        resetted_instrument.timebase_offset = -5e-8
        assert resetted_instrument.timebase_offset == -5e-8

    # Trigger
    def test_trigger_select(self, resetted_instrument):
        with pytest.raises(ValueError):
            resetted_instrument.trigger_select = "edge"
        with pytest.raises(ValueError):
            resetted_instrument.trigger_select = ("edge", "c2")
        with pytest.raises(ValueError):
            resetted_instrument.trigger_select = ("edge", "c2", "time")
        with pytest.raises(ValueError):
            resetted_instrument.trigger_select = ("ABCD", "c1", "time", 0)
        with pytest.raises(ValueError):
            resetted_instrument.trigger_select = ("edge", "c1", "time", 1000)
        with pytest.raises(ValueError):
            resetted_instrument.trigger_select = ("edge", "c1", "time", 0, 1)
        resetted_instrument.trigger_select = ("edge", "c1", "off")
        resetted_instrument.trigger_select = ("EDGE", "C1", "OFF")
        assert resetted_instrument.trigger_select == ["edge", "c1", "off"]
        resetted_instrument.trigger_select = ("glit", "c1", "p2", 1e-3, 2e-3)
        assert resetted_instrument.trigger_select == ["glit", "c1", "p2", 1e-3, 2e-3]

    # Acquisition
    @pytest.mark.parametrize("case", SAMPLING_MODES)
    def test_sampling_mode(self, resetted_instrument, case):
        if case == "Sequence":
            resetted_instrument.sampling_mode = case
            resetted_instrument.number_segments = 16
            assert resetted_instrument.sampling_mode == "Sequence"
            assert resetted_instrument.number_segments == 16
        else:
            resetted_instrument.sampling_mode = case
            assert resetted_instrument.sampling_mode == case

    def test_acquisition_sampling_rate(self, resetted_instrument):
        assert resetted_instrument.acquisition_sampling_rate == 10E+9

    # Setup methods
    @pytest.mark.parametrize("ch_number", CHANNELS)
    def test_channel_setup(self, instrument, ch_number):
        # Only autoscale on the first channel
        instrument = instrument
        if ch_number == self.CHANNELS[0]:
            instrument.reset()
            sleep(3)
            instrument.autoscale()
            sleep(5)

        # Not testing the actual values assignment since different combinations of
        # parameters can play off each other.
        expected = instrument.ch(ch_number).current_configuration
        instrument.ch(ch_number).setup()
        assert instrument.ch(ch_number).current_configuration == expected
        with pytest.raises(AttributeError):
            instrument.ch(5)
        instrument.ch(ch_number).setup(
            bwlimit="20MHz",
            coupling="dc",
            display=True,
            invert=False,
            offset=0.0,
            # probe_attenuation=10.0,
            scale=0.05,
            trigger_coupling="dc",
            trigger_level=0.150,
            # trigger_level2=0.150,
            trigger_slope="positive",
        )
        expected = {
            "channel": ch_number,
            "attenuation": 10.0,
            "bandwidth_limit": "20MHz",
            "coupling": "dc",
            "offset": 0.0,
            "display": True,
            "volts_div": 0.05,
            "inverted": False,
            "trigger_edge_coupling": "dc",
            "trigger_level": 0.150,
            # "trigger_level2": 0.150,
            "trigger_edge_slope": "positive",
        }
        actual = instrument.ch(ch_number).current_configuration
        assert actual == expected

    # Download methods
    def test_download_image_default_arguments(self, instrument):
        img = instrument.download_image()
        assert type(img) is bytearray
        # assert pytest.approx(len(img), 0.1) == 144142

    # Measurement

    # @pytest.mark.skip(reason="connect CH1 probe to ground and probe compensation connectors")
    def test_measurement_add(self, instrument):
        instrument.reset()
        sleep(3)
        instrument.autoscale()
        sleep(5)
        for (slot, meas_type), (meas, value) in \
                zip(self.MEAS_SLOTS.items(), self.EXPECTED_MEAS_VALUES.items()):
            instrument.ch(1).display_parameter = slot, meas_type
            assert instrument.ch(1).measure_parameter(slot) == pytest.approx(value, rel=0.3)

    @pytest.mark.parametrize("param_engine", PARAM_ENGINE)
    def test_measurement_configure(self, instrument, param_engine):
        instrument.measurement_configure(1, "channel1", "channel2", param_engine)
        print(instrument.measurement_result_status(1))
        assert instrument.ask("VBS? 'return=app.Measure.P1.ParamEngine'").strip() == param_engine

    def test_math_FFT(self, instrument):
        instrument.math_reset_all()
        instrument.f1.math_view = True
        instrument.f1.math_mode = "TwoOperators"
        instrument.f1.math_source1 = "C1"
        instrument.f1.math_source2 = "C2"
        instrument.f1.math_operator1 = "FFT"
        instrument.f1.math_operator2 = "Average"
        instrument.f1.math_operator2_sweeps = 10
        instrument.f1.math_operator1_FFT_output_type = "PowerSpectrum"
        instrument.f1.math_operator1_FFT_window_type = "Hamming"
