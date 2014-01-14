/*
 * Program to calculate the winner of a poker hand given two hands
 */


import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 
 * @author cpvalcourt
 */
public class Main {

	public static enum handRank {
		high_card, one_pair, two_pair, three_of_a_kind, straight, flush, full_house, four_of_a_kind, straight_flush, royal_flush;
	}

	public class Hand implements Comparable<Hand> {

		public class Card implements Comparable<Card> {
			int value;
			String suit;

			public Card(String c) {
				char face = c.charAt(0);
				suit = c.substring(1, 2);
				if ((int) face < 58 && (int) face > 49) {
					value = (int) face - 48;
				} else {
					switch (face) {
					case 'T':
						value = 10;
						break;
					case 'J':
						value = 11;
						break;
					case 'Q':
						value = 12;
						break;
					case 'K':
						value = 13;
						break;
					case 'A':
						value = 14; // Could be 1 on straight
						break;
					}
				}
			}

			@Override
			public int compareTo(Card c) {
				if (c.value < this.value) {
					return 1;
				} else if (c.value > this.value) {
					return -1;
				} else if (c.value == this.value) {
					return 0;
				}
				return 0;
			}

			@Override
			public String toString() {
				return value + suit;
			}
		}

		List<Card> cards = new ArrayList<Card>(5);
		handRank rank = handRank.high_card;
		int highCard = 0;
		int highPair=0;
		int lowPair=0;

		public Hand(List<String> inCards) {
			for (String card : inCards) {
				// System.out.println("adding card " + card);
				cards.add((new Hand.Card(card)));
			}
			rank = rankHand();
		}

		public handRank rankHand() {
			handRank rank = handRank.high_card;
			boolean isFlush = false;
			boolean isStraight = false;

			// Sort Hand
			Collections.sort(cards);

			// Set high card based on sort
			int highCard = cards.get(4).value;
			// Is Flush
			if (cards.get(0).suit.compareTo(cards.get(1).suit) == 0
					&& cards.get(0).suit.compareTo(cards.get(2).suit) == 0
					& cards.get(0).suit.compareTo(cards.get(3).suit) == 0
					&& cards.get(0).suit.compareTo(cards.get(4).suit) == 0) {
				isFlush = true;
			}
			// Ace High
			if (((cards.get(0).value + 1) == cards.get(1).value)
					&& ((cards.get(1).value + 1) == cards.get(2).value)
					&& ((cards.get(2).value + 1) == cards.get(3).value)
					&& ((cards.get(3).value + 1) == cards.get(4).value)) {
				isStraight = true;
			}
			// Ace low
			if (!isStraight && cards.get(4).value == 14
					&& (cards.get(0).value + 1 == cards.get(1).value)
					&& (cards.get(1).value + 1 == cards.get(2).value)
					&& (cards.get(2).value + 1 == cards.get(3).value)
					&& (cards.get(4).value - 12 == cards.get(0).value)) {
				isStraight = true;
				highCard = cards.get(3).value;
			}
			// MAP is <card value, number of matches>
			Map<Integer, Integer> matches = new HashMap<Integer, Integer>(5);
			Card curr;
			Card next;
			int numbOfMatches = 0;
			// If not a straight or flush, check for matches
			if (!isStraight && !isFlush) {
				// for each card, look at others to see if there's a match
				// record in matches HashMap
				for (int j = 0; j < 5; j++) {
					// get current card, search ahead for matches (anything back
					// has already been searched)
					curr = cards.get(j);
					if (matches.containsKey(curr.value)) {
						continue;
					}
					for (int k = j + 1; k < 5; k++) {
						next = cards.get(k);
						if (next.value == curr.value) {
							if (matches.containsKey(curr.value)) {
								numbOfMatches = (int) matches.get(curr.value) + 1;
								matches.put(curr.value, numbOfMatches);
								if (numbOfMatches > 2) { 
									highPair = curr.value;
								}
							} else {
								matches.put(curr.value, 2);
								//check for full house
								if (!matches.containsValue(3)) {
									if (highPair < curr.value && highPair != 0) {
										lowPair = highPair;
										highPair = curr.value;										
									}
									else if (highPair > curr.value) {
										lowPair = curr.value;
									}
									else {
										highPair = curr.value;
									}
								}
								else {
									lowPair = curr.value;
								}
							}
						}
						numbOfMatches = 0;
					}
					if (matches.containsValue(4)) {
						rank = handRank.four_of_a_kind;
					} else if (matches.containsValue(3)) {
						if (matches.containsValue(2)) {
							rank = handRank.full_house;
						} else {
							rank = handRank.three_of_a_kind;
						}
					} else if (matches.containsValue(2)) {
						if (matches.size() == 2) {
							rank = handRank.two_pair;
						} else {
							rank = handRank.one_pair;
						}
					}
				}
			} else {
				if (isStraight && isFlush) {
					if (highCard == 14) {
						rank = handRank.royal_flush;
					} else {
						rank = handRank.straight_flush;
					}
				} else if (isStraight) {
					rank = handRank.straight;
				}
			}

			return rank;
		}

		@Override
		public int compareTo(Hand n) {

			if (n.rank.ordinal() < this.rank.ordinal()) {
				return 1;
			} else if (n.rank.ordinal() > this.rank.ordinal()) {
				return -1;
			} else if (n.rank.ordinal() == this.rank.ordinal()) {
				// Check high and low pairs if same
				if (n.highPair < this.highPair) {
					return 1;
				}
				else if (n.highPair > this.highPair){ 
					return -1;
				}
				else {
					if (n.lowPair < this.lowPair) {
						return 1;
					}
					else if (n.lowPair > this.lowPair){ 
						return -1;
					} 
				}
				for (int i = 5; i > 0; i--) {
					if (n.cards.get(i - 1).value < this.cards.get(i - 1).value) {
						return 1;
					} else if (n.cards.get(i - 1).value > this.cards.get(i - 1).value) {
						return -1;
					}
				}

			}
			return 0;
		}

		@Override
		public String toString() {
			return cards.get(0) + ", " + cards.get(1) + ", " + cards.get(2)
					+ ", " + cards.get(3) + ", " + cards.get(4);
		}
	}

	public static void main(String[] args) {

		try {
			// Get File
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));
			List<String> leftHand = new ArrayList<String>(5);
			List<String> rightHand = new ArrayList<String>(5);
			Hand right;
			Hand left;
			String line;
			Main x = new Main();

			// Read each line
			while ((line = in.readLine()) != null) {
				if (line.length() == 0) {
					continue;
				}
				// Split into Array with " "(space) separator
				String[] cardArray = line.split("\\s");
				// Split Hands up 0-4, 5-9
				for (int i = 0; i < 5; i++) {
					leftHand.add(cardArray[i]);
				}
				// System.out.println(leftHand);
				left = x.new Hand(leftHand);
				for (int i = 5; i < 10; i++) {
					rightHand.add(cardArray[i]);
				}
				// System.out.println(rightHand);
				right = x.new Hand(rightHand);
				// Compare Hands, output result
				int comp = left.compareTo(right);
				//System.out.print(left + "\t" + left.rank + "\t" + right + "\t" +  right.rank + "\t");
				if (comp == 0) {
					System.out.println("none");
				} else if (comp == 1) {
					System.out.println("left");
				} else {
					System.out.println("right");
				}

				leftHand.clear();
				rightHand.clear();
			}
		} catch (IOException | NumberFormatException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}
	}
}