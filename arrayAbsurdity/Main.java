/*
 * Immutable array of size N which we know to be filled with integers ranging
 * from 0 to N-2, inclusive. Array contains exactly one duplicated entry and
 * that duplicate appears exactly twice. Find the duplicated entry.
 */
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.BitSet;

/**
 *
 * @author cpvalcourt
 */
public class Main {

    public static void main(String[] args) {
        try {
            String line;
            Integer intVal;
            int dupeValue = -1;
            BitSet fillArray;

            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));

            // Read each line into ArrayList
            while ((line = in.readLine()) != null) {
                if (line.trim().length() > 0) {
                    String[] lineArray = line.split(";");
                    if (lineArray.length > 0) {
                        int sizeOfArray = Integer.parseInt(lineArray[0]);
                        String[] inputs = lineArray[1].split(",");
                        fillArray = new BitSet(sizeOfArray);
                        fillArray.clear();
                        for (String next : inputs) {
                            intVal = Integer.parseInt(next);
                            if (fillArray.get(intVal)) {
                                dupeValue = intVal;
                                continue;
                            } else {
                                fillArray.set(intVal);
                            }
                        }
                        System.out.println(dupeValue);
                        dupeValue = -1;
                    }
                }
            }
        } catch (IOException | NumberFormatException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
