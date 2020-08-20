from unittest import TestCase

from parameterized import parameterized

from assembly_calculus.learning.components.errors import SequenceRunNotInitializedOrInMidRun, \
	IllegalOutputAreasException, NoPathException
from assembly_calculus.learning.components.input import InputStimuli
from assembly_calculus.learning.components.sequence import LearningSequence
from tests.learning.brain_test_utils import BrainTestUtils


class TestLearningSequence(TestCase):

	def setUp(self) -> None:
		self.utils = BrainTestUtils()
		self.brain = self.utils.create_brain(number_of_areas=5, number_of_stimuli=4, add_output_area=True)

	@parameterized.expand([
		(1,),
		(3,)
	])
	def test_sequence_one_run_per_iteration(self, number_of_cycles):
		area_a, area_b, area_c = self.brain.connectome.areas[:3]
		stimulus_a, stimulus_b = self.brain.connectome.stimuli[:2]
		input_stimuli = InputStimuli(self.brain, 100, area_a, area_b, verbose=False)
		sequence = LearningSequence(self.brain, input_stimuli)
		sequence.add_iteration(input_bits=[0, 1])
		sequence.add_iteration(subconnectome={stimulus_a: [area_a], stimulus_b: [area_b]})
		sequence.add_iteration(subconnectome={area_a: [area_c], area_b: [area_c]})
		sequence.add_iteration(subconnectome={area_c: [self.utils.output_area]})

		expected_iterations = [
			{
				input_stimuli[0][0]: [area_a],
				input_stimuli[1][0]: [area_b],
			},

			{
				stimulus_a: [area_a],
				stimulus_b: [area_b],
			},

			{
				area_a: [area_c],
				area_b: [area_c],
			},

			{
				area_c: [self.utils.output_area],
			},
		]
		expected_iterations = expected_iterations * number_of_cycles

		sequence.initialize_run(number_of_cycles=number_of_cycles)

		for idx, iteration in enumerate(sequence):
			self.assertEqual(expected_iterations[idx], iteration.format(input_stimuli, 0))

	def test_sequence_multiple_consecutive_runs_per_iteration(self):
		area_a, area_b, area_c = self.brain.connectome.areas[:3]
		stimulus_a, stimulus_b = self.brain.connectome.stimuli[:2]
		input_stimuli = InputStimuli(self.brain, 100, area_a, area_b, verbose=False)
		sequence = LearningSequence(self.brain, input_stimuli)
		sequence.add_iteration(input_bits=[0, 1], consecutive_runs=2)
		sequence.add_iteration(subconnectome={stimulus_a: [area_a], stimulus_b: [area_b]}, consecutive_runs=2)
		sequence.add_iteration(subconnectome={area_a: [area_c], area_b: [area_c]}, consecutive_runs=3)
		sequence.add_iteration(subconnectome={area_c: [self.utils.output_area]}, consecutive_runs=1)

		expected_iterations = [
			{
				input_stimuli[0][0]: [area_a],
				input_stimuli[1][0]: [area_b],
			},
			{
				input_stimuli[0][0]: [area_a],
				input_stimuli[1][0]: [area_b],
			},

			{
				stimulus_a: [area_a],
				stimulus_b: [area_b],
			},
			{
				stimulus_a: [area_a],
				stimulus_b: [area_b],
			},

			{
				area_a: [area_c],
				area_b: [area_c],
			},
			{
				area_a: [area_c],
				area_b: [area_c],
			},
			{
				area_a: [area_c],
				area_b: [area_c],
			},

			{
				area_c: [self.utils.output_area],
			},
		]
		sequence.initialize_run(number_of_cycles=1)
		for idx, iteration in enumerate(sequence):
			self.assertEqual(expected_iterations[idx], iteration.format(input_stimuli, 0))

	def test_sequence_with_only_stimuli(self):
		area_a, area_b, area_c = self.brain.connectome.areas[:3]
		stimulus_a, stimulus_b = self.brain.connectome.stimuli[:2]
		input_stimuli = InputStimuli(self.brain, 100, area_a, area_b, verbose=False)
		sequence = LearningSequence(self.brain, input_stimuli)
		sequence.add_iteration(subconnectome={stimulus_a: [area_a], stimulus_b: [area_b]})
		sequence.add_iteration(subconnectome={area_a: [area_c], area_b: [area_c]})
		sequence.add_iteration(subconnectome={area_c: [self.utils.output_area]})

		expected_iterations = [
			{
				stimulus_a: [area_a],
				stimulus_b: [area_b],
			},

			{
				area_a: [area_c],
				area_b: [area_c],
			},

			{
				area_c: [self.utils.output_area],
			},
		]

		sequence.initialize_run(number_of_cycles=1)
		for idx, iteration in enumerate(sequence):
			self.assertEqual(expected_iterations[idx], iteration.format(input_stimuli, 0))

	def test_sequence_with_only_input_bits(self):
		area_a, area_b, area_c = self.brain.connectome.areas[:3]
		input_stimuli = InputStimuli(self.brain, 100, area_a, area_b, verbose=False)
		sequence = LearningSequence(self.brain, input_stimuli)
		sequence.add_iteration(input_bits=[0, 1])
		sequence.add_iteration(subconnectome={area_a: [area_c], area_b: [area_c]})
		sequence.add_iteration(subconnectome={area_c: [self.utils.output_area]})

		expected_iterations = [
			{
				input_stimuli[0][0]: [area_a],
				input_stimuli[1][0]: [area_b],
			},

			{
				area_a: [area_c],
				area_b: [area_c],
			},

			{
				area_c: [self.utils.output_area],
			},
		]

		sequence.initialize_run(number_of_cycles=1)
		for idx, iteration in enumerate(sequence):
			self.assertEqual(expected_iterations[idx], iteration.format(input_stimuli, 0))

	def test_sequence_with_input_bits_and_stimuli_combines_the_dicts(self):
		area_a, area_b, area_c = self.brain.connectome.areas[:3]
		stimulus_a, stimulus_b, stimulus_c = self.brain.connectome.stimuli[:3]
		input_stimuli = InputStimuli(self.brain, 100, area_a, area_b, verbose=False,
		                             override={0: (stimulus_a, stimulus_c)})
		sequence = LearningSequence(self.brain, input_stimuli)
		sequence.add_iteration(input_bits=[0, 1], subconnectome={stimulus_a: [area_b], stimulus_b: [area_c]})
		sequence.add_iteration(subconnectome={area_a: [area_c], area_b: [area_c]})
		sequence.add_iteration(subconnectome={area_c: [self.utils.output_area]})

		expected_iterations_00 = [
			{
				stimulus_a: [area_a, area_b],
				input_stimuli[1][0]: [area_b],
				stimulus_b: [area_c]

			},

			{

				area_a: [area_c],
				area_b: [area_c]

			},

			{
				area_c: [self.utils.output_area],
			},
		]

		expected_iterations_01 = [
			{
				stimulus_a: [area_a, area_b],
				input_stimuli[1][1]: [area_b],
				stimulus_b: [area_c]

			},

			{
				area_a: [area_c],
				area_b: [area_c]

			},

			{
				area_c: [self.utils.output_area],

			},
		]

		expected_iterations_10 = [
			{
				stimulus_c: [area_a],
				input_stimuli[1][0]: [area_b],
				stimulus_a: [area_b],
				stimulus_b: [area_c],

			},

			{
				area_a: [area_c],
				area_b: [area_c]

			},

			{
				area_c: [self.utils.output_area],

			},
		]

		expected_iterations_11 = [
			{
				stimulus_c: [area_a],
				input_stimuli[1][1]: [area_b],
				stimulus_a: [area_b],
				stimulus_b: [area_c],

			},

			{
				area_a: [area_c],
				area_b: [area_c]

			},

			{
				area_c: [self.utils.output_area],

			},
		]

		sequence.initialize_run(number_of_cycles=1)
		for idx, iteration in enumerate(sequence):
			self.assertDictEqual(expected_iterations_00[idx], iteration.format(input_stimuli, 0))

		sequence.initialize_run(number_of_cycles=1)
		for idx, iteration in enumerate(sequence):
			self.assertDictEqual(expected_iterations_01[idx], iteration.format(input_stimuli, 1))

		sequence.initialize_run(number_of_cycles=1)
		for idx, iteration in enumerate(sequence):
			self.assertDictEqual(expected_iterations_10[idx], iteration.format(input_stimuli, 2))

		sequence.initialize_run(number_of_cycles=1)
		for idx, iteration in enumerate(sequence):
			self.assertDictEqual(expected_iterations_11[idx], iteration.format(input_stimuli, 3))

	def test_sequence_has_no_output_area(self):
		area_a, area_b, area_c = self.brain.connectome.areas[:3]

		input_stimuli = InputStimuli(self.brain, 100, area_a, area_b, verbose=False)
		sequence = LearningSequence(self.brain, input_stimuli)
		sequence.add_iteration(input_bits=[0, 1])
		sequence.add_iteration(subconnectome={area_a: [area_c], area_b: [area_c]})

		self.assertRaises(IllegalOutputAreasException, sequence.initialize_run, 1)

	def test_sequence_stimulus_has_no_path_to_output(self):
		area_a, area_b, area_c = self.brain.connectome.areas[:3]
		stimulus_a, stimulus_b = self.brain.connectome.stimuli[:2]
		input_stimuli = InputStimuli(self.brain, 100, area_a, area_b, verbose=False)
		sequence = LearningSequence(self.brain, input_stimuli)
		# Input bit 0 has no path to the output area
		sequence.add_iteration(subconnectome={stimulus_a: [area_a], stimulus_b: [area_b]})
		sequence.add_iteration(subconnectome={area_b: [area_c]})
		sequence.add_iteration(subconnectome={area_c: [self.utils.output_area]})

		self.assertRaises(NoPathException, sequence.initialize_run, 1)

	def test_sequence_input_bit_has_no_path_to_output(self):
		area_a, area_b, area_c = self.brain.connectome.areas[:3]
		input_stimuli = InputStimuli(self.brain, 100, area_a, area_b, verbose=False)
		sequence = LearningSequence(self.brain, input_stimuli)
		# Input bit 0 has no path to the output area
		sequence.add_iteration(input_bits=[0, 1])
		sequence.add_iteration(subconnectome={area_b: [area_c]})
		sequence.add_iteration(subconnectome={area_c: [self.utils.output_area]})

		self.assertRaises(NoPathException, sequence.initialize_run, 1)

	def test_sequence_not_initialized(self):
		area_a, area_b, area_c = self.brain.connectome.areas[:3]
		input_stimuli = InputStimuli(self.brain, 100, area_a, area_b, verbose=False)
		sequence = LearningSequence(self.brain, input_stimuli)
		sequence.add_iteration(input_bits=[0, 1])
		sequence.add_iteration(subconnectome={area_a: [area_c], area_b: [area_c]})
		sequence.add_iteration(subconnectome={area_c: [self.utils.output_area]})

		# Iterating without initializing raises an error
		with self.assertRaises(SequenceRunNotInitializedOrInMidRun):
			for iteration in sequence:
				self.assertIsNotNone(iteration)

		# Initializing and starting to iterate
		sequence.initialize_run(number_of_cycles=1)
		for iteration in sequence:
			break

		# Iterating again without re-initializing raises an error
		with self.assertRaises(SequenceRunNotInitializedOrInMidRun):
			for iteration in sequence:
				self.assertIsNotNone(iteration)
