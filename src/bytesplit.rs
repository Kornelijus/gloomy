use memchr::{self, Memchr}; // 2.4.1

pub struct ByteSplitImpl<'a> {
    iter: Memchr<'a>,
    slice: &'a [u8],
    position: usize,
    add_next: bool,
}

pub trait ByteSplit<'a> {
    fn byte_split(&'a self, separator: u8) -> ByteSplitImpl<'a>;
}

impl<'a> ByteSplit<'a> for &'a [u8] {
    fn byte_split(&'a self, separator: u8) -> ByteSplitImpl<'a> {
        ByteSplitImpl {
            iter: memchr::memchr_iter(separator, self),
            slice: self,
            position: 0,
            add_next: true,
        }
    }
}

impl<'a> Iterator for ByteSplitImpl<'a> {
    type Item = &'a [u8];
    fn next(&mut self) -> Option<Self::Item> {
        if let Some(next_position) = self.iter.next() {
            let slice = self.slice.get(self.position..next_position);
            self.position = next_position + 1;
            self.add_next = true;
            return slice;
        }

        // If the iterator is consumed check if the last part of the string
        // is missing to be added.
        if !self.add_next {
            None
        } else {
            // Use case for reading from last comma to end.
            let slice = self.slice.get(self.position..);
            self.position = self.slice.len();
            self.add_next = false;
            slice
        }
    }
}

// fn main() {
//     let s = b",hello,,,how are you, my friend,";
//     let s = &s[..];
//     for byte_str in s.byte_split(b',') {
//         println!("'{}'", std::str::from_utf8(byte_str).unwrap());
//     }
// }
