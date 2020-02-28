#include <fstream>
#include <iostream>
#include <string>

using namespace std;

int main() {
	ifstream fin("../data/hello.txt");
	if (!fin.is_open()) {
		cerr << "open file (../data/hello.txt) fail" << endl;
		return 1;
	}

	string buf;

	while (!fin.eof()) {
		fin >> buf;
		cout << buf;
		buf.clear();
	}

	return 0;
}