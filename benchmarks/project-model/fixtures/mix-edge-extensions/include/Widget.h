#import <Foundation/Foundation.h>

@interface Widget : NSObject
@property (nonatomic, copy) NSString *title;
- (NSString *)render;
@end
