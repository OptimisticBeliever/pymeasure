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

import logging
from enum import IntFlag
from datetime import datetime
from abc import ABCMeta

from pymeasure.instruments import Instrument, Channel
from pymeasure.instruments.teledyne.teledyne_oscilloscope import TeledyneOscilloscope, \
    TeledyneOscilloscopeChannel, sanitize_source, _remove_unit
from pymeasure.instruments.validators import strict_discrete_set, strict_range, \
    truncated_discrete_set

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class EXR(IntFlag):
    """ Code assignment for the Execution Error Register (EXR):

        =========  ================================================================================
        Code       Message
        =========  ================================================================================
        21         Permission error. The command cannot be executed in local mode.
        22         Environment error.
                    The oscilloscope is not configured to correctly process a command.
                   For instance, the oscilloscope cannot be set to RIS at a slow timebase.
        23         Option error. The command applies to an option which has not been installed.
        24         Unresolved parsing error.
        25         Parameter error. Too many parameters specified.
        26         Non-implemented command.
        27         Parameter missing. A parameter was expected by the command.
        30         Hex data error.
                    A non-hexadecimal character has been detected in a hex data block.
        31         Waveform error.
                    The amount of data received does not correspond to descriptor indicators.
        32         Waveform descriptor error. An invalid waveform descriptor has been detected.
        33         Waveform text error. A corrupted waveform user text has been detected.
        34         Waveform time error. Invalid RIS or TRIG time data has been detected.
        35         Waveform data error. Invalid waveform data have been detected.
        36         Panel setup error. An invalid panel setup data block has been detected.
        50*        No mass storage present when user attempted to access it.
        51*        Mass storage not formatted when user attempted to access it.
        53*        Mass storage was write protected when user attempted to create a file,
                    to delete a file, or to format the device.
        54*        Bad mass storage detected during formatting.
        55*        Mass storage root directory full. Cannot add directory.
        56*        Mass storage full when user attempted to write to it.
        57*        Mass storage file sequence numbers exhausted (999 reached).
        58*        Mass storage file not found.
        59*        Requested directory not found.
        61*        Mass storage file name not DOS compatible, or illegal file name.
        62*        Cannot write on mass storage because file name already exists.
        (*) valid only on instruments with a removable hard drive or memory card.
        =========  ================================================================================

    """
    PERMISSION_ERROR = 21
    ENVIRONMENT_ERROR = 22
    OPTION_ERROR = 23
    UNRESOLVED_PARSING_ERROR = 24
    PARAMETER_ERROR = 25
    NON_IMPLEMENTED_COMMAND = 26
    PARAMETER_MISSING = 27
    HEX_DATA_ERROR = 30
    WAVEFORM_ERROR = 31
    WAVEFORM_DESCRIPTOR_ERROR = 32
    WAVEFORM_TEXT_ERROR = 33
    WAVEFORM_TIME_ERROR = 34
    WAVEFORM_DATA_ERROR = 35
    PANEL_SETUP_ERROR = 36
    NO_MASS_STORAGE = 50
    MASS_STORAGE_NOT_FORMATTED = 51
    MASS_STORAGE_WRITE_PROTECTED = 53
    BAD_MASS_STORAGE_DETECTED_DURING_FORMATTING = 54
    MASS_STORAGE_ROOT_DIRECTORY_FULL = 55
    MASS_STORAGE_FULL = 56
    MASS_STORAGE_FILE_SEQUENCE_NUMBERS_EXHAUSTED = 57
    MASS_STORAGE_FILE_NOT_FOUND = 58
    REQUESTED_DIRECTORY_NOT_FOUND = 59
    MASS_STORAGE_FILE_NAME_NOT_DOS_COMPATIBLE_OR_ILLEGAL_FILE_NAME = 61
    MASS_STORAGE_BECAUSE_FILE_NAME_ALREADY_EXISTS = 62


class DDR(IntFlag):
    """ Code assignment for the Device Specific Error Register (DDR):

        =========  ===========================================
        Bit       Message
        =========  ===========================================
        13         Timebase hardware failure detected.
        12         Trigger hardware failure detected.
        11         Channel 4 hardware failure detected.
        10         Channel 3 hardware failure detected.
        9          Channel 2 hardware failure detected.
        8          Channel 1 hardware failure detected.
        7          External input overload condition detected.
        3          Channel 4 overload condition detected.
        2          Channel 3 overload condition detected.
        1          Channel 2 overload condition detected.
        0          Channel 1 overload condition detected.
        =========  ==========================================

    """
    CHANNEL_1_OVERLOAD = 1 << 0
    CHANNEL_2_OVERLOAD = 1 << 1
    CHANNEL_3_OVERLOAD = 1 << 3
    CHANNEL_4_OVERLOAD = 1 << 4
    EXTERNAL_INPUT_OVERLOAD = 1 << 7
    CHANNEL_1_HARDWARE_FAILURE = 1 << 8
    CHANNEL_2_HARDWARE_FAILURE = 1 << 9
    CHANNEL_3_HARDWARE_FAILURE = 1 << 10
    CHANNEL_4_HARDWARE_FAILURE = 1 << 11
    TRIGGER_HARDWARE_FAILURE = 1 << 12
    TIMEBASE_HARDWARE_FAILURE = 1 << 13


class CMR(IntFlag):
    """ Code assignment for the Command Error Register (CMR):

        =========  ================================================================
        Code       Message
        =========  ================================================================
         0         Command succeeded.
         1         Unrecognized command/query header.
         2         Illegal header path.
         3         Illegal number.
         4         Illegal number suffix.
         5         Unrecognized keyword.
         6         String error.
         7         GET embedded in another message.
         10        Arbitrary data block expected.
         11        Non-digit character in byte count field of arbitrary data block.
         12        EOI detected during definite length data block transfer.
         13        Extra bytes detected during definite length data block transfer.
        =========  ================================================================

    """
    COMMAND_SUCCEEDED = 0
    UNRECOGNIZED_CMD_QUERY_HEADER = 1
    ILLEGAL_HEADER_PATH = 2
    ILLEGAL_NUMBER_SUFFIX = 3
    UNRECOGNIZED_KEYWORD = 4
    STRING_ERROR = 5
    BET_EMBEDDED_IN_ANOTHER_MESSAGE = 6
    ARBITRARY_DATA_BLOCK_EXPECTED = 7
    NON_DIGIT_CHR_IN_ARBITRARY_DATA_BLOCK_BYTE_CNT_FIELD = 10
    EIO_DETECTED_DURING_DEFINITE_DATA_BLOCK_TRANSFER = 11
    TRIGGER_LINK_BUS_ERROR = 12
    EXTRA_BYTES_DETECTED_DURING_DEFINITE_LENGTH_DATA_BLOCK_TRANSFER = 13


def _math_define_validator(value, values):
    """
    Validate the input of the math_define property
    :param value: input parameters as a 3-element tuple
    :param values: allowed space for each parameter
    """
    if not isinstance(value, tuple):
        raise ValueError('Input value {} of trigger_select should be a tuple'.format(value))
    if len(value) != 3:
        raise ValueError('Number of parameters {} different from 3'.format(len(value)))
    output = (sanitize_source(value[0]), value[1], sanitize_source(value[2]))
    for i in range(3):
        strict_discrete_set(output[i], values=values[i])
    return output


def _measurement_add_validator(value, values):
    """
    Validate the input of the measurement_add property
    :param value: input parameters as a 2-element tuple
    :param values: allowed space for each parameter
    """
    if not isinstance(value, tuple):
        raise ValueError('Input value {} of measurement_add should be a tuple'.format(value))
    if len(value) != 2:
        raise ValueError('Number of parameters {} different from 2'.format(len(value)))
    output = (strict_range(value[0], values[0]), strict_discrete_set(value[1], values[1]))
    return output


def _measure_delay_validator(value, values):
    """
    Validate the input of the measure_delay property
    :param value: input parameters as a 3-element tuple
    :param values: allowed space for each parameter
    """
    if not isinstance(value, tuple):
        raise ValueError('Input value {} of trigger_select should be a tuple'.format(value))
    if len(value) != 3:
        raise ValueError('Number of parameters {} different from 3'.format(len(value)))
    output = (value[0], sanitize_source(value[1]), sanitize_source(value[2]))
    if output[1][0] > output[2][0]:
        raise ValueError(f'First channel number {output[1]} must be <= than second one {output[2]}')
    for i in range(3):
        strict_discrete_set(output[i], values=values[i])
    return output


def _bwl_select_get_process(value):
    """Search the channel BWL in the value
    value=C1,200MHZ,C2,OFF,C3,OFF,C4,OFF\n
    """
    # response_list = value.strip('\n').split(",")
    channel_index = value.index("C1")
    return value[channel_index + 1]


class LecroyWR606ZiChannel(TeledyneOscilloscopeChannel):
    """Implementation of a Lecroy WR606Zi Oscilloscope channel."""

    TRIGGER_SLOPES = {"negative": "NEG", "positive": "POS", "either": "EIT"}

    def insert_id(self, command):
        """Override the method"""
        if command[0:3] == "VBS" or command[0:5] == "PACU ":
            return command.format_map({self.placeholder: self.id})
        else:
            return "C%d:%s" % (self.id, command)

    label = Instrument.control(
        "VBS? 'return=app.Acquisition.C{ch}.LabelsText",
        "VBS 'app.Acquisition.C{ch}.LabelsText=\"%s\"",
        """Control the LabelsText attached to the displayed waveform for
           the specified channel.
        """,
    )

    view_label = Instrument.control(
        "VBS? 'return=app.Acquisition.C{ch}.ViewLabels",
        "VBS 'app.Acquisition.C{ch}.ViewLabels=%s",
        """Control whether the user-defined labels for the trace are visible.
        """,
        values={True: -1, False: 0},
        map_values=True,
    )

    bwlimit = Instrument.control(
        "VBS? 'return=app.Acquisition.C{ch}.BandwidthLimit",
        "VBS 'app.Acquisition.C{ch}.BandwidthLimit=\"%s\"",
        """Control the bandwidth limit for input channel in Hz.

        Available arguments depend upon the instrument and the attached accessories.
        """,
        validator=strict_discrete_set,
        values={"20MHz": "20MHz", "200MHz": "200MHz", "1GHz": "Full"},
        map_values=True,
    )

    coupling = Instrument.control(
        "VBS? 'return=app.Acquisition.C{ch}.Coupling",
        "VBS 'app.Acquisition.C{ch}.Coupling=\"%s\"",
        """Control the input coupling.

        Note that coupling choices vary between instrument models. 
        WavePro 7000 instruments for example support AC1M and DC1M
        modes in addition to DC50 and GND choices.
        """,
        validator=strict_discrete_set,
        values={"ac": "AC1M", "dc": "DC1M", "dc50": "DC50", "ground": "Gnd"},
        map_values=True,
    )

    invert = Instrument.control(
        "VBS? 'return=app.acquisition.C{ch}.Invert",
        "VBS 'app.acquisition.C{ch}.Invert=%s",
        """Control the inversion of the input signal.""",
        validator=strict_discrete_set,
        values={True: -1, False: 0},
        map_values=True,
    )

    trigger_level = Instrument.control(
        "VBS? 'return=app.Acquisition.Trigger.C{ch}.Level",
        "VBS 'app.Acquisition.Trigger.C{ch}.Level=%g",
        """Control the lower trigger level voltage for the specified source (float).
        Higher and lower trigger levels are used with runt/slope triggers.
        When setting the trigger level it must be divided by the probe attenuation. This is
        not documented in the datasheet and it is probably a bug of the scope firmware.
        An out-of-range value will be adjusted to the closest legal value.
        """,
        get_process=_remove_unit,
    )

    trigger_level2 = Instrument.control(
        "VBS? 'return=app.Acquisition.Trigger.C{ch}.Level2",
        "VBS 'app.Acquisition.Trigger.C{ch}.Level2=%g",
        """Control the upper trigger level voltage for the specified source (float).
        Higher and lower trigger levels are used with runt/slope triggers.
        When setting the trigger level it must be divided by the probe attenuation. This is
        not documented in the datasheet and it is probably a bug of the scope firmware.
        An out-of-range value will be adjusted to the closest legal value.
        Only valid when trigger type is Runt, SlewRate.
        """,
        get_process=_remove_unit,
    )

    average_sweeps = Instrument.control(
        "VBS? 'return=app.Acquisition.C{ch}.AverageSweeps'",
        "VBS 'app.Acquisition.C{ch}.AverageSweeps=\"%d\"'",
        """Control the number of averaging sweeps.
        This is distinct from the math function app.Math.Fx.
        If the number of sweeps is 1 (the default value), the data will not be averaged.""",
        validator=strict_range,
        values=[1, 1000000],
    )

    @property
    def current_configuration(self):
        """Get channel configuration as a dict containing the following keys:

        - "channel": channel number (int)
        - "attenuation": probe attenuation (float)
        - "bandwidth_limit": bandwidth limiting enabled (bool)
        - "coupling": "ac 1M", "dc 1M", "ground" coupling (str)
        - "offset": vertical offset (float)
        - "display": currently displayed (bool)
        - "volts_div": vertical divisions (float)
        - "trigger_edge_coupling": trigger coupling can be "dc" "ac" "highpass" "lowpass" (str)
        - "trigger_level": trigger level (float)
        - "trigger_edge_slope": trigger slope can be "negative" "positive" "window" (str)
        """

        ch_setup = {
            "channel": self.id,
            "attenuation": self.probe_attenuation,
            "bandwidth_limit": self.bwlimit,
            "coupling": self.coupling,
            "offset": self.offset,
            "display": self.display,
            "volts_div": self.scale,
            "inverted": self.invert,
            "trigger_edge_coupling": self.trigger_coupling,
            "trigger_level": self.trigger_level,
            "trigger_edge_slope": self.trigger_slope
        }
        return ch_setup

    _measurable_parameters = ["PKPK", "MAX", "MIN", "AMPL", "TOP", "BASE", "CMEAN", "MEAN", "RMS",
                              "CRMS", "OVSN", "FPRE", "OVSP", "RPRE", "PER", "FREQ", "PWID",
                              "NWID", "RISE", "FALL", "WID", "DUTY", "NDUTY", "ALL"]

    display_parameter = Instrument.setting(
        "PACU %d,%s,C{ch}",
        """Set the waveform processing of this channel with the specified algorithm and the result
        is displayed on the front panel.
        :param1 is the P1 through P8 parameters. possible values are 1 to 8
        :param2 the parameter (measurement on a trace) for Px.

        The param2 accepts the following parameters:
        =========   ===================================
        Parameter   Description
        =========   ===================================
        PKPK        vertical peak-to-peak
        MAX         maximum vertical value
        MIN         minimum vertical value
        AMPL        vertical amplitude
        TOP         waveform top value
        BASE        waveform base value
        CMEAN       average value in the first cycle
        MEAN        average value
        RMS         RMS value
        CRMS        RMS value in the first cycle
        OVSN        overshoot of a falling edge
        FPRE        preshoot of a falling edge
        OVSP        overshoot of a rising edge
        RPRE        preshoot of a rising edge
        PER         period
        FREQ        frequency
        PWID        positive pulse width
        NWID        negative pulse width
        RISE        rise-time
        FALL        fall-time
        WID         Burst width
        DUTY        positive duty cycle
        NDUTY       negative duty cycle
        ALL         All measurement
        =========   ===================================
        """,
        validator=_measurement_add_validator,
        values=[[1, 8], _measurable_parameters]
    )

    def measure_parameter(self, slot: int):
        """Process a waveform with the selected algorithm and returns the specified measurement.

        :param slot: reflect the P1 to P8 parameters
        """
        slot = strict_range(value=slot, values=[1, 8])
        output = self.ask("PAVA? CUST%d" % slot)
        match = self._re_pava_response.match(output)
        if match:
            if match.group('parameter') != str(slot):
                raise ValueError(f"Parameter {match.group('parameter')} different from {slot}")
            if match.group('state') and match.group('state') == 'IV':
                raise ValueError(f"Parameter state for {slot} is invalid")
            return float(match.group('value'))
        else:
            raise ValueError(f"Cannot extract value from output {output}")


class LecroyOscilloscopeMathChannel(Channel, metaclass=ABCMeta):
    """Implementation of a Lecroy WR606Zi Oscilloscope math channel."""

    _BOOLS = {True: 1, False: 0}

    _math_operators = ["AbsoluteValue", "Average", "Boxcar", "Copy", "Correlation", "Demodulate",
                       "Derivative", "Deskew", "Difference", "EnhancedResolution", "Envelope",
                       "ExcelMath", "Exp", "Exp10", "FastWavePort", "FFT", "Filter", "Floor",
                       "Histogram", "Htie2BER", "I2SToWform", "Integral", "Interpolate", "Invert",
                       "ISIPatt", "Ln", "Log10", "LowPassIIR", "MathcadMath", "MATLABWaveform",
                       "Null", "PersistenceHistogram", "PersistenceTraceMean",
                       "PersistenceTraceRange", "PersistenceTraceSigma", "Product", "Ratio",
                       "Reciprocal", "Reframe", "Rescale", "Roof", "SegmentSelect", "SeqBuilder",
                       "SequenceAverage", "SinXOverX", "Sparse", "Square", "SquareRoot", "Sum",
                       "Track", "Trend", "Trk", "WaveScript", "Zoom"]

    math_define = Instrument.control(
        "F{ch}:DEF?", "F{ch}:DEF EQN,'%s%s%s'",
        """Control the desired waveform math operation between two channels.

        Three parameters must be passed as a tuple:

        #. source1 : source channel on the left
        #. operation : operator must be "*", "/", "+", "-"
        #. source2 : source channel on the right

        """,
        validator=_math_define_validator,
        values=[["C1", "C2", "C3", "C4"], ["*", "/", "+", "-"], ["C1", "C2", "C3", "C4"]]
    )

    math_view = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.View'",
        "VBS 'app.Math.F{ch}.View=%d'",
        """Control whether the trace of math function is visible.
        Note that even when math traces are not visible,
        but are being used as inputs to other math functions and/or measurements,
        they are computed.""",
        validator=strict_discrete_set,
        values={True: 1, False: 0},
        map_values=True,
    )

    math_mode = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.MathMode'",
        "VBS 'app.Math.F{ch}.MathMode=\"%s\"'",
        """Control the math mode.""",
        validator=strict_discrete_set,
        values=["Graphing", "OneOperator", "TwoOperators", "WebEdit"]
    )

    math_source1 = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Source1'",
        "VBS 'app.Math.F{ch}.Source1=\"%s\"'",
        """Control the first source of the first operator.
        Note that the two possible sources of Operator1 are Source1 and Source2,
        Source3 is the second source to Operator2, with the first source of Operator2
        being the output of Operator1.""",
        validator=strict_discrete_set,
        values=['C1', 'C2', 'C3', 'C4']
    )

    math_source2 = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Source1'",
        "VBS 'app.Math.F{ch}.Source2=\"%s\"'",
        """Control the second source of the first operator.""",
        validator=strict_discrete_set,
        values=['C1', 'C2', 'C3', 'C4']
    )

    math_operator1 = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Operator1'",
        "VBS 'app.Math.F{ch}.Operator1=\"%s\"'",
        """Control the first operator of math function.""",
        validator=strict_discrete_set,
        values=_math_operators,
    )

    math_operator2 = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Operator2'",
        "VBS 'app.Math.F{ch}.Operator2=\"%s\"'",
        """Control the second operator of math function.""",
        validator=strict_discrete_set,
        values=_math_operators,
    )

    math_zoom_horizontal_position = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Zoom.HorPos'",
        "VBS 'app.Math.F{ch}.Zoom.HorPos=\"%f\"'",
        """Control the horizontal position of center of the grid on the zoomed trace.
        The unit of measurement is the screen width, that is, 0.3 means a shift of
        three of the ten divisions. A positive value moves the trace to the left.""",
        validator=strict_range,
        values=[-0.5, 0.5],
    )

    math_zoom_horizontal_zoom = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Zoom.HorZoom'",
        "VBS 'app.Math.F{ch}.Zoom.HorZoom=\"%f\"'",
        """Control the horizontal magnification of the trace.
        The magnification will be in a 1 2 5 10 sequence unless
        variable horizontal magnification has been set.""",
        validator=strict_range,
        values=[0.1, 1.000E+6],
    )

    math_zoom_horizontal_variable = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Zoom.VariableHorZoom'",
        "VBS 'app.Math.F{ch}.Zoom.VariableHorZoom=\"%s\"'",
        """Control the ability to zoom horizontally by a continuously variable factor.
        Note that if a horizontal zoom of 0.9 is set, while variable zoom is off,
        the horizontal zoom will be set to 1.0. If the variable zoom is then enabled,
        the factor of 0.9 will have been remembered, and it will be used.
        Note that the previous value will not be remembered during a power-cycle.""",
        validator=strict_discrete_set,
        values=_BOOLS,
    )

    math_zoom_vertical_variable = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Zoom.VariableVerZoom'",
        "VBS 'app.Math.F{ch}.Zoom.VariableVerZoom=\"%s\"'",
        """Control the ability to zoom vertically by a continuously variable factor.
        Note that if a vertical zoom of 0.9 is set, while variable zoom is off,
        the horizontal zoom will be set to 1.0. If the variable zoom is then enabled,
        the factor of 0.9 will have been remembered, and it will be used.
        Note that the previous value will not be remembered during a power-cycle.""",
        validator=strict_discrete_set,
        values=_BOOLS,
    )

    math_zoom_vertical_position = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Zoom.VerPos'",
        "VBS 'app.Math.F{ch}.Zoom.VerPos=\"%f\"'",
        """Control the vertical position of center of the grid on the zoomed trace.
        The unit of measurement is the screen height, that is, 0.375 means a shift
        of three of the eight divisions. A positive value moves the trace downwards.""",
        validator=strict_range,
        values=[-1.5, 1.5],
    )

    math_zoom_vertical_zoom = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Zoom.VerZoom'",
        "VBS 'app.Math.F{ch}.Zoom.VerZoom=\"%f\"'",
        """Control the vertical magnification of the trace.
        The magnification will be in a 1 2 5 10 sequence unless
        VariableVerZoom has been set to True, in which case it
        will be continuously variable.""",
        validator=strict_range,
        values=[0.1, 100],
    )

    math_operator1_average_type = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Operator1Setup.AverageType'",
        "VBS 'app.Math.F{ch}.Operator1Setup.AverageType=\"%s\"'",
        """Control the averaging mode.""",
        validator=strict_discrete_set,
        values=["Summed", "Continuous"],
    )

    math_operator2_average_type = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Operator2Setup.AverageType'",
        "VBS 'app.Math.F{ch}.Operator2Setup.AverageType=\"%s\"'",
        """Control the averaging mode.""",
        validator=strict_discrete_set,
        values=["Summed", "Continuous"],
    )

    math_operator1_clear_sweeps = Instrument.setting(
        "VBS 'app.Math.F{ch}.Operator1Setup.ClearSweeps'",
        """Control Clears all averaged sweeps.""",
    )

    math_operator2_clear_sweeps = Instrument.setting(
        "VBS 'app.Math.F{ch}.Operator2Setup.ClearSweeps'",
        """Control Clears all averaged sweeps.""",
    )

    math_operator1_sweeps = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Operator1Setup.Sweeps'",
        "VBS 'app.Math.F{ch}.Operator1Setup.Sweeps=\"%d\"'",
        """Control he number of sweeps to be averaged when trace is set to
        averaging - continuous or summed.""",
        validator=strict_range,
        values=[1, 1000000],
    )

    math_operator2_sweeps = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Operator2Setup.Sweeps'",
        "VBS 'app.Math.F{ch}.Operator2Setup.Sweeps=\"%d\"'",
        """Control he number of sweeps to be averaged when trace is set to
        averaging - continuous or summed.""",
        validator=strict_range,
        values=[1, 1000000],
    )

    # FFT
    math_operator1_FFT_algorithm = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Operator1Setup.Algorithm'",
        "VBS 'app.Math.F{ch}.Operator1Setup.Algorithm=\"%s\"'",
        """Control the algorithm for the FFT.""",
        validator=strict_discrete_set,
        values=["LeastPrime", "Power2"],
    )

    math_operator1_FFT_fill_type = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Operator1Setup.FillType'",
        "VBS 'app.Math.F{ch}.Operator1Setup.FillType=\"%s\"'",
        """Control the algorithm for the FFT.""",
        validator=strict_discrete_set,
        values=["LeastPrime", "Power2"],
    )

    math_operator1_FFT_supressdc = Instrument.setting(
        "VBS 'app.Math.F{ch}.Operator1Setup.SuppressDC=%d",
        """Control suppression of the value at zero frequency in the FFT spectrum.""",
        validator=strict_discrete_set,
        values={True: 1, False: 0},
        map_values=True
    )

    math_operator1_FFT_output_type = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Operator1Setup.Type'",
        "VBS 'app.Math.F{ch}.Operator1Setup.Type=\"%s\"'",
        """Control the ouptput type of FFT spectrum""",
        validator=strict_discrete_set,
        values=["Magnitude", "Phase", "PowerSpectrum"]
    )

    math_operator1_FFT_window_type = Instrument.control(
        "VBS? 'return=app.Math.F{ch}.Operator1Setup.Window'",
        "VBS 'app.Math.F{ch}.Operator1Setup.Window=\"%s\"'",
        """Control the type of window for the FFT.""",
        validator=strict_discrete_set,
        values=["BlackmanHarris", "FlatTop", "Hamming", "Rectangular", "VonHann"]
    )


class LecroyWR606Zi(TeledyneOscilloscope):
    """Represents the Lecroy WR606Zi Oscilloscope interface for interacting with the instrument.

    Refer to the Lecroy WR606Zi Oscilloscope Programmer's Guide for further details about
    using the lower-level methods to interact directly with the scope.

    This implementation is based on the shared base class :class:`TeledyneOscilloscope`.

    Attributes:

        WRITE_INTERVAL_S: minimum time between two commands. If a command is received less than
        WRITE_INTERVAL_S after the previous one, the code blocks until at least WRITE_INTERVAL_S
        seconds have passed.
        Because the oscilloscope takes a non-negligible time to perform some operations, it might
        be needed for the user to tweak the sleep time between commands.
        The WRITE_INTERVAL_S is set to 10ms as default however its optimal value heavily depends
        on the actual commands and on the connection type, so it is impossible to give a unique
        value to fit all cases. An interval between 10ms and 500ms second proved to be good,
        depending on the commands and connection latency.

    .. code-block:: python

        scope = LecroyWR606Zi(resource)
        scope.autoscale()
        ch1_data_array, ch1_preamble = scope.download_waveform(source="C1", points=2000)
        # ...
        scope.shutdown()
    """

    _BOOLS = {True: "ON", False: "OFF"}

    WRITE_INTERVAL_S = 0.02  # seconds
    TRIGGER_TYPES = {"edge": "EDGE", "pulse": "WIDTH", "interval": "INTERVAL", "runt": "RUNT",
                     "slewrate": "SLEWRATE", "glitch": "GLITCH", "pattern":  "PATTERN",
                     "dropout": "DROPOUT", "tv": "TV"}
    ANALOG_TRIGGER_SOURCE = {"channel1": "C1", "channel2": "C2", "channel3": "C3",
                             "channel4": "C4", "external": "EXT", "line": "LINE"}
    DIGITAL_TRIGGER_SOURCE = ['D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7',
                              'D8', 'D9', 'D10', 'D11', 'D12', 'D13', 'D14', 'D15',
                              'D16', 'D17', 'D18', 'D19', 'D20', 'D21', 'D22', 'D23',
                              'D24', 'D25', 'D26', 'D27', 'D28', 'D29', 'D30', 'D31',
                              'D32', 'D33', 'D34', 'D35']

    _measurable_parameters = ["Amplitude", "Area", "Base", "Cycles", "Delay", "DeltaDelay",
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
                              "HistogramMean", "HistogramMedian", "HistogramMid",
                              "HistogramMinimum", "HistogramRms", "HistogramSdev", "HistogramTop",
                              "HoldTime", "HParamScript", "I2StoValue", "LastPoint", "LevelAtX",
                              "LocalBase", "LocalBaselineSeparation", "LocalMaximum",
                              "LocalMinimum", "LocalNumber", "LocalPeakToPeak",
                              "LocalTimeAtMaximum", "LocalTimeAtMinimum", "LocalTimeBetweenEvent",
                              "LocalTimeBetweenPeaks", "LocalTimeBetweenTroug",
                              "LocalTimeOverThreshold", "LocalTimePeakToTrough",
                              "LocalTimeTroughToPeak", "LocalTimeUnderThreshol", "MathcadParam",
                              "MATLABParameter", "Maximum", "MaximumPopulation", "Mean", "Median",
                              "Minimum", "Mode", "NarrowBandPhase", "NarrowBandPower",
                              "NCycleJitter", "NonLinearTransitionShift", "npoints", "Null",
                              "NumberOfModes", "OvershootNegative", "OvershootPositive",
                              "Overwrite", "ParamScript", "PEAKMAG", "Peaks", "PeakToPeak",
                              "Percentile", "Period", "PeriodAtLevel", "Phase", "PopulationAtX",
                              "PowerFactor", "Protocol2Analog", "Protocol2Protocol",
                              "Protocol2Value", "ProtocolBitrate", "ProtocolLoad",
                              "ProtocolNumMessages", "PW50", "PW50Negative", "PW50Positive",
                              "Range", "RealPower", "Resolution", "Rise", "Rise2080",
                              "RiseAtLevel", "RootMeanSquare", "SAS", "Setup", "Skew", "Slew",
                              "StandardDeviation", "TAA", "TAANegative", "TAAPositive", "TIE",
                              "TimeAtCAN", "TimeAtLevel", "TimeAtProtocol", "Top",
                              "TotalPopulation", "tUpS", "Width", "WidthAtLevel", "WidthNegative",
                              "XAtMaximum", "XAtMinimum", "XAtPeak"]

    ch_1 = Instrument.ChannelCreator(LecroyWR606ZiChannel, 1)

    ch_2 = Instrument.ChannelCreator(LecroyWR606ZiChannel, 2)

    ch_3 = Instrument.ChannelCreator(LecroyWR606ZiChannel, 3)

    ch_4 = Instrument.ChannelCreator(LecroyWR606ZiChannel, 4)

    functions = Instrument.MultiChannelCreator(LecroyOscilloscopeMathChannel, list(range(1, 9)),
                                               prefix="f")

    def __init__(self, adapter, name="Lecroy WR606Zi Oscilloscope", **kwargs):
        super().__init__(adapter, name, **kwargs)

    event_status_enable_bits = Instrument.control(
        "*ESE?", "*ESE %d",
        """Control the Standard Event Status Enable Register bits.

        The register can be queried using the :meth:`~.query_event_status_register` method. Valid
        values are between 0 and 255. Refer to the instrument manual for an explanation of the bits.
        """,
        values=[0, 255],
        validator=strict_range,
        cast=int,
    )

    def query_event_status_register(self):
        """ Query the value of the Standard Event Status Register.

        Note that querying this value, clears the register. Refer to the instrument manual for an
        explanation of the returned value.
        """
        return self.values("*ESR?", cast=int)[0]

    service_request_enable_bits = Instrument.control(
        "*SRE?", "*SRE %d",
        """Control the Service Request Enable Register bits.

        Valid values are between 0 and 255; setting 0 performs a register reset. Refer to the
        instrument manual for an explanation of the bits.
        """,
        values=[0, 255],
        validator=strict_range,
        cast=int,
    )

    def check_set_errors(self):
        """
        Method to read the error registers
        """
        errors_list = []
        esr = self.query_event_status_register()
        if esr & (1 << 4):  # Bit 4 Execution error detected
            execution_error = self.execution_error
            errors_list.append(execution_error.name)
            raise Warning(f'Execution error {execution_error.name}')
        elif esr & (1 << 3):  # Bit 3 Device dependent error occurred.
            device_error = self.device_error
            errors_list.append(device_error.name)
            raise Warning(f'Device error {device_error.name}')
        elif esr & (1 << 5):  # Bit 5 Command parser error detected.
            command_error = self.command_error
            errors_list.append(command_error.name)
            raise Warning(f'Device error {command_error.name}')
        else:
            return errors_list

    command_error = Instrument.measurement(
        "CMR?",
        """Checks the command error register""",
        get_process=lambda v: CMR(int(v)),
    )

    execution_error = Instrument.measurement(
        "EXR?",
        """Checks the execution error register""",
        get_process=lambda v: EXR(int(v)),
    )

    device_error = Instrument.measurement(
        "DDR?",
        """Checks the device error register""",
        get_process=lambda v: DDR(int(v)),
    )

    ##################
    # Timebase Setup #
    ##################

    horizontal_offset_origin = Instrument.control(
        "VBS? 'return=app.Acquisition.Horizontal.HorOffsetOrigin",
        "VBS 'app.Acquisition.Horizontal.HorOffsetOrigin=\"%g\"",
        """the origin, in graticule divisions, of the time scale in which HorOffset is measured.
        The value 0 corresponds to the left edge of the graticule.
        The value 10 corresponds to the right edge of the graticule.
        """,
        validator=strict_range,
        values=[0, 10],
    )

    horizontal_offset = Instrument.control(
        "VBS? 'return=app.Acquisition.Horizontal.HorOffset",
        "VBS 'app.Acquisition.Horizontal.HorOffset=\"%g\"",
        """Control the horizontal position of the trigger time,
        relative to the origin set by HorOffsetOrigin, in seconds.
        Positive to the right, negative to the left.
        """,
    )

    @property
    def timebase(self):
        """Get timebase setup as a dict containing the following keys:

            - "timebase_scale": horizontal scale in seconds/div (float)
            - "timebase_offset": interval in seconds between the trigger and the reference
              position (float)

        """
        tb_setup = {
            "timebase_scale": self.timebase_scale,
            "timebase_offset": self.timebase_offset,
        }
        return tb_setup

    def timebase_setup(self, scale=None, offset=None):
        """Set up timebase. Unspecified parameters are not modified. Modifying a single parameter
        might impact other parameters. Refer to oscilloscope documentation and make multiple
        consecutive calls to timebase_setup if needed.

        :param scale: interval in seconds between the trigger event and the reference position.
        :param offset: horizontal scale per division in seconds/div.
        """

        if scale is not None:
            self.timebase_scale = scale
        if offset is not None:
            self.timebase_offset = offset

    ###############
    # Acquisition #
    ###############

    sampling_mode = Instrument.control(
        "VBS? 'return=app.Acquisition.Horizontal.SampleMode",
        "VBS 'app.Acquisition.Horizontal.SampleMode=\"%s\"",
        """Control the mode of acquisition.
        Choose from Real Time, Sequence, RIS, or Roll mode.
        """,
        validator=strict_discrete_set,
        values=["RealTime", "Sequence", "RIS", "Roll"],
    )

    number_segments = Instrument.control(
        "VBS? 'return=app.Acquisition.Horizontal.NumSegments",
        "VBS 'app.Acquisition.Horizontal.NumSegments=%d",
        """Control the number of segments in the sequence mode of acquisition.
        Only valid when sampling_mode is Sequence""",
        validator=strict_range,
        values=[2, 10000]
    )

    acquisition_sampling_rate = Instrument.measurement(
        "VBS? 'return=app.Acquisition.Horizontal.SamplingRate",
        """Get the sample rate of the scope."""
    )

    ##################
    #    Waveform    #
    ##################

    memory_size = Instrument.control(
        "MSIZ?", "MSIZ %s",
        """Control the maximum depth of memory.

        <size>:={7K,70K,700K,7M} for non-interleaved mode. Non-interleaved means a single channel is
        active per A/D converter. Most oscilloscopes feature two channels per A/D converter.

        <size>:={14K,140K,1.4M,14M} for interleave mode. Interleave mode means multiple active
        channels per A/D converter.
        """,
        validator=truncated_discrete_set,
        values=[{500: "0.5K", 1e3: "1K", 25e2: "2.5K", 5e3: "5K", 1e4: "10K", 25e3: "25k",
                 5e4: "50K", 1e5: "100K", 25e4: "250K", 5e5: "500K", 1e6: "1M", 25e5: "2.5M",
                 5e6: "5M", 1e7: "10M", 16e5: "16M"}, ],
        map_values=True,
    )

    #################
    # Download data #
    #################

    def hardcopy_setup(self, **kwargs):
        """Specify hardcopy settings.

        Connect a printer or define how to save to file. Set any or all
        of the following parameters.

        :param device: {BMP, JPEG, PNG, TIFF}
        :param format: {PORTRAIT, LANDSCAPE}
        :param background: {Std, Print, BW}
        :param destination: {PRINTER, CLIPBOARD, EMAIL, FILE, REMOTE}
        :param area: {GRIDAREAONLY, DSOWINDOW, FULLSCREEN}
        :param directory: Any legal DOS path, for FILE mode only
        :param filename: Filename string, no extension, for FILE mode only
        :param printername: Valid printer name, for PRINTER mode only
        :param portname: {GPIB, NET}
        """
        keys = {
            "device": "DEV",
            "format": "FORMAT",
            "background": "BCKG",
            "destination": "DEST",
            "area": "AREA",
            "directory": "DIR",
            "filename": "FILE",
            "printername": "PRINTER",
            "portname": "PORT",
        }

        arg_strs = [keys[key] + "," + value for key, value in kwargs.items()]
        self.write("HCSU " + ",".join(arg_strs))

    def download_image(self):
        """Get an image of oscilloscope screen in bytearray of specified file format."""
        self.hardcopy_setup(device="BMP", format="LANDSCAPE", background="BW",
                            destination="REMOTE", area="FULLSCREEN", directory="C:\\Temp",
                            filename="screenshot", portname="NET")
        self.write("SCDP")
        img = self.read_bytes(count=-1, break_on_termchar=True)
        dt = datetime.now()
        fileName = dt.strftime("C:\\Temp\\LECROY_%Y%m%d_%H%M%S.BMP")
        # Save image data to local disk
        file = open(fileName, "wb")
        file.write(img)
        file.close()
        return bytearray(img)

    ###############
    #   Trigger   #
    ###############

    trigger_source = Instrument.control(
        "VBS? 'return=app.Acquisition.Trigger.Source",
        "VBS 'app.Acquisition.Trigger.Source=\"%s\"",
        """Control the source trigger.""",
        validator=strict_discrete_set,
        values=ANALOG_TRIGGER_SOURCE,
        map_values=True,
        dynamic=True,
    )

    trigger_type = Instrument.control(
        "VBS? 'return=app.Acquisition.Trigger.Type",
        "VBS 'app.Acquisition.Trigger.Type=\"%s\"",
        """Control the trigger type.""",
        validator=strict_discrete_set,
        values=TRIGGER_TYPES,
        map_values=True,
        dynamic=True,
        preprocess_reply=lambda v: v.upper(),
    )

    def center_trigger(self):
        """Set the trigger levels to center of the trigger source waveform."""
        self.horizontal_offset = 0
        self.horizontal_offset_origin = 5

    ###############
    #    Math     #
    ###############

    def math_clear_sweeps(self):
        """Control sweeps for history functions such as average, histogram and trend.
                See also the general 'app.ClearSweeps' control which clears accumulated data
                for all subsystems, including persistence, measurement statistics, etc."""
        self.write("VBS 'app.Math.ClearSweeps'")

    def math_reset_all(self):
        """Set the math subsystem to its default state.
                All currently selected math operators, and other settings will be lost."""
        self.write("VBS 'app.Math.ResetAll'")

    ###############
    #   Measure   #
    ###############

    measurement_mode = Instrument.control(
        "VBS? 'return=app.Measure.MeasureMode'",
        "VBS 'app.Measure.MeasureMode=\"%s\"",
        """Control the measurement mode""",
        validator=strict_discrete_set,
        values=["MyMeasure", "StdVertical", "StdHorizontal"],
    )

    measurement_type = Instrument.setting(
        "VBS 'app.Measure.P%d.ParamEngine=\"%s\"'",
        """Control the parameter (measurement on a trace) for Px.
        This setting applies only if the MeasurementType control is set to "measure".
        """,
        validator=_measurement_add_validator,
        values=[[1, 8], _measurable_parameters],
        check_set_errors=True,
    )

    def measurement_result_curracq(self, slot):
        """Get the last value."""
        self.write(f'VBS? \'return=app.Measure.P{slot}.last.Result.Value')
        return float(self.read().strip('\n'))

    def measurement_result_allacqs_mean(self, slot):
        """Get the mean value for all accumulated
        measurement acquisitions."""
        self.write(f'VBS? \'return=app.Measure.P{slot}.mean.Result.Value')
        return float(self.read().strip('\n'))

    def measurement_result_allacqs_max(self, slot):
        """Get the maximum value for all accumulated
        measurement acquisitions."""
        self.write(f'VBS? \'return=app.Measure.P{slot}.max.Result.Value')
        return float(self.read().strip('\n'))

    def measurement_result_allacqs_min(self, slot):
        """Get the minimum value for all accumulated
        measurement acquisitions."""
        self.write(f'VBS? \'return=app.Measure.P{slot}.min.Result.Value')
        return float(self.read().strip('\n'))

    def measurement_result_allacqs_stddev(self, slot):
        """Get the standard deviation for all accumulated
        measurement acquisitions."""
        self.write(f'VBS? \'return=app.Measure.P{slot}.sdev.Result.Value')
        return float(self.read().strip('\n'))

    def measurement_result_allacqs_population(self, slot):
        """Get the population measurement value."""
        self.write(f'VBS? \'return=app.Measure.P{slot}.num.Result.Value')
        return int(self.read().strip('\n'))

    def measurement_result_status(self, slot):
        """Get the measurement status description"""
        self.write(f'VBS? \'return=app.Measure.P{slot}.Out.Result.StatusDescription')
        return self.read().strip('\n')

    def measurement_clear_all(self) -> None:
        """Resets all parameter setups, turning each of the parameters view to off
        the MeasurementType to measure and the selected paramEngine to Null."""
        self.write("VBS 'app.Measure.ClearAll'")

    def measurement_configure(self, slot: int, source1, source2, meas_type):
        """Configure the measurement

        :param slot: int measurement slot number
        :param source1: str channel measurement source
        :param source2: str second channel source
        :param meas_type: str measurement type"""
        slot = strict_range(slot, [1, 8])
        source1 = strict_discrete_set(source1, self.ANALOG_TRIGGER_SOURCE)
        source1 = self.ANALOG_TRIGGER_SOURCE[source1]
        source2 = strict_discrete_set(source2, self.ANALOG_TRIGGER_SOURCE)
        source2 = self.ANALOG_TRIGGER_SOURCE[source2]
        meas_type = strict_discrete_set(meas_type, self._measurable_parameters)
        self.write(f"VBS 'app.Measure.P{slot}.View=True'")
        self.write(f"VBS 'app.Measure.ShowMeasure=True'")
        self.write(f"VBS 'app.Measure.P{slot}.Source1=\"{source1}\"'")
        self.write(f"VBS 'app.Measure.P{slot}.Source2=\"{source2}\"'")
        self.measurement_type = (slot, meas_type)
