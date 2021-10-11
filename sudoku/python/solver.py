##=- solver.py -================================================================
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##==============================================================================

import sys, os, math

##==============================================================================
# Helper Functions
##==============================================================================

# Read specific sudoku file into 2D list.
def read_sudoku():
  args = sys.argv
  try:
    with open(args[1], "r") as f:
      sudoku_list = []
      for curr_row in f.readlines():
        # Read sudoku file into a 2D list.
        curr_list = list(map(lambda t: int(t),
                             curr_row.replace('\n', '').split()))
        sudoku_list.append(curr_list)
      return sudoku_list
  except Exception as e:
    sys.exit(e)

# Read minisat result file into list.
def read_result(minisat_result_file):
  try:
    with open(minisat_result_file, "r") as f:
      lines = f.readlines()
      second_line = lines[1]
      result_list = list(map(lambda t: int(t),
                             second_line.replace('\n', '').split()))
      return result_list
  except Exception as e:
    sys.exit(e)

# Solve the sudoku problem with minisat
# Note: minisat is the submodule of this project, please build minisat first.
def call_minisat(cnf_file, minisat_result_file):
  os.system(
    f"../../minisat/build/release/bin/minisat {cnf_file} {minisat_result_file}")

##==============================================================================
# Encoder and Decoder
##==============================================================================

# Encode sudoku in CNF term.
def encode(size, row, col, val):
  return (row - 1) * size * size + (col - 1) * size + val

# Decode and get result from minisat result.
def decode(ele, sudoku_size):
  row = math.ceil(ele / (sudoku_size * sudoku_size)) - 1
  row_tmp = ele - (row * sudoku_size * sudoku_size)
  col = math.ceil(row_tmp / sudoku_size) - 1
  val = row_tmp - (col * sudoku_size)
  return int(row), int(col), int(val)

##==============================================================================
# Generator
##==============================================================================

# Generate CNF file based on the rules.
def generate_cnf(sudoku_list, cnf_file):
  sudoku_size = len(sudoku_list)
  term = sudoku_size * sudoku_size * sudoku_size
  clause = 0
  # Perform rules and calculate the number of clause.
  with open(cnf_file, "w") as f:
    row_rule_clause = row_rule(f, sudoku_size, clause)
    col_rule_clause = col_rule(f, sudoku_size, row_rule_clause)
    block_rule_clause = block_rule(f, sudoku_size, col_rule_clause)
    unique_rule_clause = unique_rule(f, sudoku_size, block_rule_clause)
    curr_sudoku_clause = curr_sudoku(f, sudoku_list, unique_rule_clause)
  with open(cnf_file, "r+") as n:
    old = n.read()
    n.seek(0)
    n.write("p cnf " + str(term) + " " + str(curr_sudoku_clause) + "\n")
    n.writelines(old)

# Generate result file.
def generate_result(sudoku_result_file, result_list, sudoku_list):
  sudoku_size = len(sudoku_list)
  curr_row = 0
  with open(sudoku_result_file, "w") as f:
    for res in result_list:
      if res > 0:
        row, col, val = decode(res, sudoku_size)
        if row == curr_row:
          f.write(str(val) + " ")
        else:
          f.write("\n" + str(val) + " ")
          curr_row = row

##==============================================================================
# Rules
##==============================================================================

def row_rule(f, sudoku_size, clause):
  for row in range(sudoku_size):
    for val in range(sudoku_size):
      for col in range(sudoku_size):
        res = encode(sudoku_size, row + 1, col + 1, val + 1)
        f.write(str(res) + " ")
      f.write(str(0) + "\n")
      clause += 1
  return clause

def col_rule(f, sudoku_size, clause):
  for col in range(sudoku_size):
    for val in range(sudoku_size):
      for row in range(sudoku_size):
        res = encode(sudoku_size, row + 1, col + 1, val + 1)
        f.write(str(res) + " ")
      f.write(str(0) + "\n")
      clause += 1
  return clause

def block_rule(f, sudoku_size, clause):
  block_size = int(math.sqrt(sudoku_size))
  # Select block.
  for r in range(block_size):
    for s in range(block_size):
      # Select number.
      for val in range(sudoku_size):
        # Select element in the block.
        for i in range(block_size):
          for j in range(block_size):
            res = encode(sudoku_size, block_size * r + i + 1,
                         block_size * s + j + 1, val + 1)
            f.write(str(res) + " ")
        f.write(str(0) + "\n")
        clause += 1
  return clause


def unique_rule(f, sudoku_size, clause):
  for row in range(sudoku_size):
    for col in range(sudoku_size):
      for val in range(sudoku_size):
        for non_val in range(sudoku_size):
          if val != non_val:
            val_res = encode(sudoku_size, row + 1, col + 1, val + 1)
            non_val_res = encode(sudoku_size, row + 1, col + 1, non_val + 1)
            f.write(str(-val_res) + " " + str(-non_val_res) + " 0\n")
            clause +=1
  return clause

# Describe current sudoku status.
def curr_sudoku(f, sudoku_list, clause):
  sudoku_size = len(sudoku_list)
  for row in range(sudoku_size):
    for col in range(sudoku_size):
      ele = sudoku_list[row][col]
      if ele != 0:
        res = encode(sudoku_size, row + 1, col + 1, ele)
        f.write(str(res) + " 0\n")
        clause += 1
  return clause

##==============================================================================
# Main Function
##==============================================================================

def main():
  # Read sudoku as list.
  input_list = read_sudoku()
  # Define the name of generated files.
  cnf_file = "sudoku.cnf"
  minisat_result_file = "minisat-result.txt"
  sudoku_result_file = "sudoku-result.txt"
  # Encode the sudoku rules and generate CNF file.
  generate_cnf(input_list, cnf_file)
  # Solve the sudoku with minisat and generate the solution.
  call_minisat(cnf_file, minisat_result_file)
  # Read the solution as list.
  result_list = read_result(minisat_result_file)
  # Decode the solution and generate the result file.
  result = generate_result(sudoku_result_file, result_list, input_list)

if __name__ == "__main__":
  main()
